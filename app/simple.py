import time, datetime, os, logging, subprocess, sys, statistics
import serial

import power

# Sensor Sampling Environment Variables
PORT = os.environ.get('GAGE_SERIAL_PORT', '/dev/ttyS2')
UART = os.environ.get('GAGE_SERIAL_UART', 'UART2')
STORAGE_MOUNT_PATH = os.environ.get('GAGE_STORAGE_MOUNT_PATH', '/mnt/gagedata')
WAIT = int(os.environ.get('GAGE_SAMPLE_WAIT', 5))
SENSOR_LOW = int(os.environ.get('GAGE_SENSOR_LOW', 501))
SENSOR_HIGH = int(os.environ.get('GAGE_SENSOR_HIGH', 9998))
MIN_SAMPLES = int(os.environ.get('GAGE_MIN_SAMPLES', 10))
MAX_ATTEMPTS = int(os.environ.get('GAGE_MAX_ATTEMPTS', 100))
MAX_STD_DEV = int(os.environ.get('GAGE_MAX_STD_DEV', 100))


# Power control Environment Variables
POWER_CONSERVE = bool(os.environ.get('GAGE_POWER_CONSERVE', False))
RESTART_TIME = int(os.environ.get('GAGE_RESTART_TIME', 900))
WATCHDOG_RESET_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_RESET_TIMEOUT', 300))
WATCHDOG_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_POWER_TIMEOUT', 300))
WATCHDOG_STOP_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_STOP_POWER_TIMEOUT', 300))
WATCHDOG_START_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_START_POWER_TIMEOUT', 300))
STARTUP_REASONS = os.environ.get('GAGE_STARTUP_REASONS')


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

def serial_setup():
    """ enable UART-2 device tree overlay in cape manager """
    output = subprocess.run(
        [f'''sh -c "echo 'BB-{UART}' > /sys/devices/platform/bone_capemgr/slots"'''], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'I/O error' in output.stderr.decode('utf-8'):
        logger.info(f'{UART} already enabled in capemgr')
    elif len(output.stderr) > 0:
        logger.error(f'Other error occured adding {UART} to capemgr', output)
    else:
        logger.info(f'{UART} added to capemgr')
    ser = serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)
    return ser

def cell_setup():
    """ Loads kernel modules and cycles USB bus to enumerate cell modem """
    output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

    # If the module isn't detected
    if 'Sierra' not in output.stdout.decode('ASCII'):
        # load kernel modules
        output = subprocess.run(['modprobe sierra'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output = subprocess.run(['modprobe sierra_net'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

        # cycle USB bus
        output = subprocess.run(
            ['sh -c "echo 0 > /sys/bus/usb/devices/1-1/authorized"'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
        output = subprocess.run(
            ['sh -c "echo 1 > /sys/bus/usb/devices/1-1/authorized"'],
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
        )
        output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if 'Sierra' in output.stdout.decode('ASCII'):
            logger.info('Sierra Cell Modem USB kernel drivers loaded and modem detected')
        else:
            logger.error('Unable to load Sierra Cell Modem kernel drivers')
    else:
        logger.info('Sierra Cell Modem USB kernel drivers already loaded and modem detected')


def read_serial(ser):
    """Make 50 attempts to read the sensor serial data. Returns the first valid response"""
    for _ in range(50):
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit(): # and data[1:5] != '9999'
                return int(data[1:5])
        logger.debug('Serial returned invalid info, trying again')
    logger.error('Serial did not return valid info in 50 tries')
    raise SensorError

def clean_sample_mean(sample_func, ser, low, high, min_samples, max_attempts, max_std_dev):
    """With a given sampling_func, sample and discard outliers"""
    samples = [sample_func(ser)] # initial sample so that stdev doesn't yell at us for too few samples

    for n in range(max_attempts):
        samples.append(sample_func(ser))

        cleaned_low_high = [s for s in samples if low <= s <= high]
        try:
            cleaned = [s for s 
                        in cleaned_low_high 
                        if abs(statistics.mean(cleaned_low_high) - s) < 2 * statistics.stdev(cleaned_low_high)]
        except statistics.StatisticsError:
            cleaned = []

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

def sensor_cycle(ser):
    """Collect and log sensor data once"""
    try:
        distance = clean_sample_mean(read_serial, ser, SENSOR_LOW, SENSOR_HIGH, MIN_SAMPLES, MAX_ATTEMPTS, MAX_STD_DEV)
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


def mount_data_sd(path):
    """Mounts the microsd card for data storage at given path"""
    try:
        os.mkdir(path)
    except OSError:
        logger.info(f'{path} already exists. Storage should be mounted')
    else:
        logger.info(f'Created mount point for microsd at {path}')
    
    output = subprocess.run([f'mount {path}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if f"mount can't find {path} in /etc/fstab" in output.stderr.decode('ASCII'):
        logger.error("/etc/fstab doesn't include mount {path}")
    elif f'is already mounted on {path}' in output.stderr.decode('ASCII'):
        logger.info(f'MicroSD storage already mounted at {path}')
    else:
        logger.info(f'MicroSD storage mounted at {path}')
    


    

if __name__ == '__main__':
    mount_data_sd(STORAGE_MOUNT_PATH)
    cell_setup()
    ser = serial_setup()
    if not POWER_CONSERVE:
        while True:
            sensor_cycle(ser)