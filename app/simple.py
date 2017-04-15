import time, datetime, os, logging, subprocess, sys, statistics, csv
import serial

import power, pcape
from cell import sprint

# Sensor Sampling Environment Variables
PORT = os.environ.get('GAGE_SERIAL_PORT', '/dev/ttyS2')
UART = os.environ.get('GAGE_SERIAL_UART', 'UART2')
STORAGE_MOUNT_PATH = os.environ.get('GAGE_STORAGE_MOUNT_PATH', '/mnt/gagedata')
DATA_CSV_FOLDER = os.environ.get('GAGE_DATA_CSV_FOLDER', STORAGE_MOUNT_PATH + '/logs/')
MAX_LOG_FILES = int(os.environ.get('MAX_LOG_FILES', 3))
WAIT = int(os.environ.get('GAGE_SAMPLE_WAIT', 5))
MIN_VOLTAGE = float(os.environ.get('GAGE_MIN_VOLTAGE', 3.2))
CELL_TYPE = os.environ.get('GAGE_CELL_TYPE', 'ting-sierra-250u')

SENSOR_LOW = int(os.environ.get('GAGE_SENSOR_LOW', 501))
SENSOR_HIGH = int(os.environ.get('GAGE_SENSOR_HIGH', 9998))
MIN_SAMPLES = int(os.environ.get('GAGE_MIN_SAMPLES', 10))
MAX_ATTEMPTS = int(os.environ.get('GAGE_MAX_ATTEMPTS', 100))
MAX_STD_DEV = int(os.environ.get('GAGE_MAX_STD_DEV', 100))


# Power control Environment Variables
POWER_CONSERVE = bool(os.environ.get('GAGE_POWER_CONSERVE', False))
RESTART_TIME = int(os.environ.get('GAGE_RESTART_TIME', 14))
WATCHDOG_RESET_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_RESET_TIMEOUT', 300))
WATCHDOG_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_POWER_TIMEOUT', 300))
WATCHDOG_STOP_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_STOP_POWER_TIMEOUT', 300))
WATCHDOG_START_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_START_POWER_TIMEOUT', 300))
STARTUP_REASONS = os.environ.get('GAGE_STARTUP_REASONS', '0x09')


logger = logging.getLogger('gage')
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)


class SensorError(Exception):
    pass

class SamplingError(Exception):
    pass

class TooFewSamples(SamplingError):
    pass


def writerow(row):
    """Write a row to the current csv file"""
    with open(DATA_CSV_PATH, 'a') as f:
        writer = csv.writer(f)
        writer.writerow(row)


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
            flow = 'charging'
        elif amps < 2:
            flow = 'float'
        else:
            flow = 'discharging'
        logger.info(f'{date} {distance}mm {volts}v {flow} {amps}ma')
        writerow((date, distance, 'mm ultrasound', volts, flow, amps))
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
    


def remove_old_log_files():
    """Removes log files older than MAX_LOG_FILES"""
    ordered = sorted((DATA_CSV_FOLDER + filename for filename in os.listdir(DATA_CSV_FOLDER)), key=os.path.getctime, reverse=True)
    old = ordered[MAX_LOG_FILES:]
    for path in old:
        logger.info(f'Removing log {path} as there are more than MAX_LOG_FILES ({MAX_LOG_FILES}).')
        os.remove(path)
    

if __name__ == '__main__':
    if POWER_CONSERVE:
        pcape.set_wdt_power(WATCHDOG_POWER_TIMEOUT)

    # setup cell
    sprint.Sierra250U()
    
    # mount SD and clean out old log files
    mount_data_sd(STORAGE_MOUNT_PATH)
    try:
        os.mkdir(DATA_CSV_FOLDER)
    except OSError:
        logger.info(f'Log directory {DATA_CSV_FOLDER} already exists')
    else:
        logger.info(f'Created log directory {DATA_CSV_FOLDER}')
    remove_old_log_files()
    DATA_CSV_PATH = DATA_CSV_FOLDER + datetime.date.today().isoformat() + '.csv'

    # set startup reasons
    pcape.set_startup_reasons(STARTUP_REASONS)

    # setup serial
    ser = serial_setup()

    if not POWER_CONSERVE:
        while True:
            sensor_cycle(ser)