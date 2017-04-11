import time, datetime, os, logging, subprocess, sys, statistics
import serial

import power

PORT = '/dev/ttyS2'
WAIT = int(os.environ.get('GAGE_SIMPLE_WAIT', 5))
SENSOR_LOW = int(os.environ.get('GAGE_SENSOR_LOW', 500))
SENSOR_HIGH = int(os.environ.get('GAGE_SENSOR_HIGH', 9999))
MIN_SAMPLES = int(os.environ.get('GAGE_MIN_SAMPLES', 10))
MAX_ATTEMPTS = int(os.environ.get('GAGE_MAX_ATTEMPTS', 100))
MAX_STD_DEV = int(os.environ.get('GAGE_MAX_STD_DEV', 100))


logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class SensorError(Exception):
    pass


class SamplingError(Exception):
    pass

class TooFewSamples(SamplingError):
    pass

# enable UART-2 device tree overlay in cape manager
output = subprocess.run(
    ['''sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"'''], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
if 'I/O error' in output.stderr.decode('utf-8'):
    logger.info('UART-2 already enabled in capemgr')
elif len(output.stderr) > 0:
    logger.error('Other error occured adding UART-2 to capemgr', output)
else:
    logger.info('UART-2 added to capemgr')


ser = serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)

def read_serial():
    for _ in range(50):
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit(): # and data[1:5] != '9999'
                return int(data[1:5])
        logger.debug('Serial returned invalid info, trying again')
    logger.error('Serial did not return valid info in 50 tries')
    raise SensorError

def clean_sample_mean(sample_func, low, high, min_samples, max_attempts, max_std_dev):
    samples = [sample_func()] # initial sample so that stdev doesn't yell at us for too few samples

    for n in range(max_attempts):
        samples.append(sample_func())

        cleaned_low_high = [s for s in samples if low < s < high]
        try:
            cleaned = [s for s 
                        in cleaned_low_high 
                        if abs(statistics.mean(cleaned_low_high) - s) < 2 * statistics.stdev(cleaned_low_high)]
        except statistics.StatisticsError:
            pass

        if len(cleaned) >= min_samples:
            if statistics.stdev(cleaned) < max_std_dev:
                return statistics.mean(cleaned)
    
    if len(cleaned) < min_samples:
        if low in samples:
            raise TooFewSamples(f'Too few cleaned samples that were not too low ({low})')
        elif high in samples:
            raise TooFewSamples(f'Too few cleaned samples that were not too high ({high})')
        else:
            raise TooFewSamples('Too few cleaned samples')
    
    stdev = round(statistics.stdev(cleaned), 2)
    raise SamplingError(f'Stdev ({stdev}) did not meet criteria ({max_std_dev}) in {max_attempts}')

if __name__ == '__main__':
    while True:
        try:
            distance = clean_sample_mean(read_serial, SENSOR_LOW, SENSOR_HIGH, MIN_SAMPLES, MAX_ATTEMPTS, MAX_STD_DEV)
        except SamplingError as e:
            date = datetime.datetime.now()
            logger.error(f'{date} - Sampling error - {e}')
        else:
            date = datetime.datetime.now()
            volts = round(power.checkVolts(), 2)
            amps = round(power.checkAmps(), 2)
            if amps < 0:
                amps = f'charging {amps}'
            elif amps < 2:
                amps = f'float {amps}'
            else:
                amps = f'discharging {amps}'
            logger.info(f'{date} {distance}mm {volts}v {amps}ma')
            time.sleep(WAIT)