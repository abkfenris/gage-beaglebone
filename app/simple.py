import time, datetime, os, logging, subprocess, sys, statistics, csv, importlib
import serial
from logging.handlers import RotatingFileHandler

import cell, config, power, pcape, supervisor
from cell import sprint
from gage_client.gage_client import Client
from utils import uptime

# Sensor Sampling Environment Variables
PORT = os.environ.get('GAGE_SERIAL_PORT', '/dev/ttyS2')
UART = os.environ.get('GAGE_SERIAL_UART', 'UART2')
STORAGE_MOUNT_PATH = os.environ.get('GAGE_STORAGE_MOUNT_PATH', '/mnt/gagedata')
DATA_CSV_FOLDER = os.environ.get('GAGE_DATA_CSV_FOLDER', STORAGE_MOUNT_PATH + '/logs/')
FILE_LOG_FOLDER = os.environ.get('GAGE_FILE_LOG_FOLDER', STORAGE_MOUNT_PATH + '/syslogs/')
MAX_LOG_FILES = int(os.environ.get('MAX_LOG_FILES', 10))
WAIT = int(os.environ.get('GAGE_SAMPLE_WAIT', 5))
MIN_VOLTAGE = float(os.environ.get('GAGE_MIN_VOLTAGE', 3.0))
CELL_TYPE = os.environ.get('GAGE_CELL_TYPE', 'cell.sprint.Sierra250U')
SAMPLES_PER_RUN = int(os.environ.get('GAGE_SAMPLES_PER_RUN', 10))
PRE_SHUTDOWN_TIME = int(os.environ.get('GAGE_PRE_SHUTDOWN_TIME', 30))
MAX_UPDATE_WAIT = int(os.environ.get('GAGE_MAX_UPDATE_WAIT', 300))
INVERT_SAMPLE = bool(os.environ.get('GAGE_INVERT_SAMPLE', False))

SENSOR_LOW = int(os.environ.get('GAGE_SENSOR_LOW', 501))
SENSOR_HIGH = int(os.environ.get('GAGE_SENSOR_HIGH', 9998))
MIN_SAMPLES = int(os.environ.get('GAGE_MIN_SAMPLES', 10))
MAX_ATTEMPTS = int(os.environ.get('GAGE_MAX_ATTEMPTS', 100))
MAX_STD_DEV = int(os.environ.get('GAGE_MAX_STD_DEV', 100))

SUBMIT_ID = int(os.environ.get('GAGE_SUBMIT_ID'))
SUBMIT_KEY = os.environ.get('GAGE_SUBMIT_KEY')
SUBMIT_URL = os.environ.get('GAGE_SUBMIT_URL')

# Power control Environment Variables
POWER_CONSERVE = bool(os.environ.get('GAGE_POWER_CONSERVE', False))
RESTART_TIME = int(os.environ.get('GAGE_RESTART_TIME', 10))
MIN_VOLTAGE_RESTART_TIME = int(os.environ.get('GAGE_MIN_VOLTAGE_RESTART_TIME', 25))
WATCHDOG_RESET_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_RESET_TIMEOUT', 300))
WATCHDOG_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_POWER_TIMEOUT', 300))
WATCHDOG_STOP_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_STOP_POWER_TIMEOUT', 600))
WATCHDOG_START_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_START_POWER_TIMEOUT', 120))
STARTUP_REASONS = os.environ.get('GAGE_STARTUP_REASONS', '0x09')

MAX_UPTIME = int(os.environ.get('GAGE_MAX_UPTIME', WATCHDOG_STOP_POWER_TIMEOUT * 2))

# Logging levels
STDOUT_LOG_LEVEL = os.environ.get('GAGE_STDOUT_LOG_LEVEL', 'WARNING').upper()
FILE_LOG_LEVEL = os.environ.get('GAGE_FILE_LOG_LEVEL', 'INFO').upper()


# Testing Environment Variables
TESTING_NO_CELL = os.environ.get('TESTING_NO_CELL')





log_levels = {'DEBUG': logging.DEBUG,
              'INFO': logging.INFO,
              'WARNING': logging.WARNING,
              'ERROR': logging.ERROR,
              'CRITICAL': logging.CRITICAL}

logger = logging.getLogger('gage')
logger.setLevel(logging.DEBUG)

formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')

ch = logging.StreamHandler(sys.stdout)
ch.setLevel(log_levels.get(config.STDOUT_LOG_LEVEL, logging.WARNING))
ch.setFormatter(formatter)
logger.addHandler(ch)

if config.SENTRY_DSN:
    logger.info('setting up Sentry logging')
    from raven import Client as Raven_Client
    from raven.handlers.logging import SentryHandler

    raven_client = Raven_Client(config.SENTRY_DSN, 
                                name = config.RESIN_DEVICE_NAME,
                                environment = config.RESIN_APP_NAME,
                                auto_log_stacks = True,
                                tags = {
                                    'python version': config.RESIN_PYTHON_VERSION,
                                    'supervisor version': config.RESIN_SUPERVISOR_VERSION,
                                    'resin app release': config.RESIN_APP_RELEASE
                                })
    raven_handler = SentryHandler(raven_client)
    raven_handler.setLevel(log_levels.get(config.SENTRY_LOG_LEVEL, logging.WARNING))

    logger.addHandler(raven_handler)
    

class SensorError(Exception):
    pass

class SamplingError(Exception):
    pass

class TooFewSamples(SamplingError):
    pass


def writerow(row):
    """Write a row to the current csv file"""
    if DATA_CSV_PATH:
        with open(DATA_CSV_PATH, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    else:
        logger.warning(f'DATA_CSV_PATH not avaliable, would have written: {row}')


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

def sensor_cycle(ser, client):
    """Collect and log sensor data once"""
    try:
        distance = clean_sample_mean(read_serial, ser, SENSOR_LOW, SENSOR_HIGH, MIN_SAMPLES, MAX_ATTEMPTS, MAX_STD_DEV)
        if INVERT_SAMPLE:
            distance = SENSOR_HIGH - distance
    except SamplingError as e:
        date = datetime.datetime.now()
        logger.error(f'{date} - Sampling error - {e}')
        distance = None
    date = datetime.datetime.now()
    volts = round(power.checkVolts(), 2)
    amps = round(power.checkAmps(), 2)

    if distance:
        client.reading('level', str(date), distance)
        client.reading('volts', str(date), volts)
        client.reading('amps', str(date), amps)

    if amps < 0:
        flow = 'charging'
    elif amps < 2:
        flow = 'float'
    else:
        flow = 'discharging'

    logger.info(f'{distance}mm {volts}v {flow} {amps}ma')
    writerow((date, distance, 'mm ultrasound', volts, flow, amps))

    time.sleep(WAIT)


def mount_data_sd(path):
    """Mounts the microsd card for data storage at given path"""
    try:
        os.mkdir(path)
    except OSError:
        logger.debug(f'{path} already exists. Storage should be mounted')
    else:
        logger.debug(f'Created mount point for microSD at {path}')
    
    output = subprocess.run([f'mount {path}'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if f"mount can't find {path} in /etc/fstab" in output.stderr.decode('ASCII'):
        logger.error("/etc/fstab doesn't include mount {path}")
    elif f'is already mounted on {path}' in output.stderr.decode('ASCII'):
        logger.debug(f'MicroSD storage already mounted at {path}')
    else:
        logger.debug(f'MicroSD storage mounted at {path}')
    

def sd_avaliable():
    """ Returns True if the SD card block device is avaliable to the system """
    output = subprocess.run('fdisk -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return 'mmcblk0' in output.stdout.decode('ASCII')


def remove_old_log_files():
    """Removes log files older than MAX_LOG_FILES"""
    ordered = sorted((DATA_CSV_FOLDER + filename for filename in os.listdir(DATA_CSV_FOLDER)), key=os.path.getctime, reverse=True)
    old = ordered[MAX_LOG_FILES:]
    for path in old:
        logger.info(f'Removing log {path} as there are more than MAX_LOG_FILES ({MAX_LOG_FILES}).')
        os.remove(path)

def log_network_info():
    """ Log current network status and toggle LEDs """
    connections = cell.list_active_connections()
    for conn in connections:
        logger.debug(conn)
    
    if len(connections) > 0:
        leds.led_2 = True # network connection avaliable
    else:
        leds.led_2 = False


if __name__ == '__main__':
    #if POWER_CONSERVE:
    #    pcape.set_wdt_power(WATCHDOG_POWER_TIMEOUT)
    
    pcape.set_system_time()
    pcape.set_wdt_power(WATCHDOG_STOP_POWER_TIMEOUT)
    pcape.set_wdt_start(WATCHDOG_START_POWER_TIMEOUT)
    

    leds = pcape.StatusLEDs()
    leds.led_1, leds.led_2 = False, False

    # mount SD and clean out old log files
    SD_CARD = sd_avaliable()
    
    if SD_CARD:
        logger.debug('SD block storage avaliable, attempting to mount')
        mount_data_sd(STORAGE_MOUNT_PATH)

        try:
            os.mkdir(DATA_CSV_FOLDER)
        except OSError:
            logger.debug(f'Log directory {DATA_CSV_FOLDER} already exists')
        else:
            logger.debug(f'Created log directory {DATA_CSV_FOLDER}')
        
        try:
            os.mkdir(FILE_LOG_FOLDER)
        except OSError:
            logger.debug(f'Syslog directory {FILE_LOG_FOLDER} already exists')
        else:
            logger.debug(f'Created syslog directory {FILE_LOG_FOLDER}')
        
        # set up file logging
        fh = RotatingFileHandler(FILE_LOG_FOLDER + 'syslog', maxBytes=10000000, backupCount=MAX_LOG_FILES)
        fh.setLevel(log_levels.get(FILE_LOG_LEVEL, logging.DEBUG))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Is the stop file present on the SD card
        STOP = os.path.isfile(STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            remove_old_log_files()
        
        DATA_CSV_PATH = DATA_CSV_FOLDER + datetime.date.today().isoformat() + '.csv'
        
        leds.led_1 = True # SD Card mounted and avaliable for storage
    else:
        logger.error('Micro SD card not avaliable for file storage')
        DATA_CSV_PATH = False
        STOP = False
    
    if power.checkVolts() < MIN_VOLTAGE:
        logger.error(f'System voltage has fallen below minimum voltage specified ({MIN_VOLTAGE} V). Shutting down for {MIN_VOLTAGE_RESTART_TIME} min to charge.')
        
        pcape.set_startup_reasons(STARTUP_REASONS)
        pcape.set_cape_time()
        pcape.set_time(MIN_VOLTAGE_RESTART_TIME)

        supervisor.shutdown()

    if uptime() > MAX_UPTIME and POWER_CONSERVE:
        logger.error(f'System has been up for longer than the maximum allowed uptime ({uptime()} > {MAX_UPTIME} seconds). Shutting down.')

        pcape.set_startup_reasons(STARTUP_REASONS)
        pcape.set_cape_time()
        pcape.set_time(RESTART_TIME)

        supervisor.shutdown()

    if not TESTING_NO_CELL:
        # setup cell
        cell_module_str, cell_method_str = CELL_TYPE.rsplit('.', 1)

        cell_module = importlib.import_module(cell_module_str)
        Cell_Modem = getattr(cell_module, cell_method_str)

        cell_modem = Cell_Modem()
    
    # setup serial
    ser = ultrasonic.serial_setup()

    # setup client for submission
    client = Client(SUBMIT_URL, SUBMIT_ID, SUBMIT_KEY)

    if POWER_CONSERVE and not STOP:
        pcape.set_wdt_power(WATCHDOG_STOP_POWER_TIMEOUT)
        
        for n in range(SAMPLES_PER_RUN):
            sensor_cycle(ser, client)
            
            log_network_info()
        
        logger.info(f'Sensing for {PRE_SHUTDOWN_TIME} more seconds to allow communication.')
        pcape.set_wdt_power(WATCHDOG_STOP_POWER_TIMEOUT)

        for n in range(PRE_SHUTDOWN_TIME // WAIT):
            sensor_cycle(ser, client)

            log_network_info()
        
        #pcape.set_time(WATCHDOG_START_POWER_TIMEOUT)

        if pcape.update_in_progress():
            for x in range(MAX_UPDATE_WAIT // WAIT):
                pcape.set_wdt_power(WATCHDOG_STOP_POWER_TIMEOUT)
                logger.info(f'Update in progress: {pcape.update_percentage()}%. Giving it {MAX_UPDATE_WAIT} more seconds.')
                MAX_UPDATE_WAIT -= WAIT
                sensor_cycle(ser, client)
                
                log_network_info()

                if not pcape.update_in_progress():
                    break
        else:
            logger.debug('No update scheduled, getting ready to shutdown')

        client.send_all()

        STOP = os.path.isfile(STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            # set startup reasons
            pcape.set_startup_reasons(STARTUP_REASONS)
            pcape.set_cape_time()
            pcape.set_time(RESTART_TIME)

            logger.debug('Powercape info:')
            for line in pcape.powercape_info():
                logger.debug('   ' + line)
            
            leds.led_1, leds.led_2 = False, False

            supervisor.shutdown()
    
    else:
        while True:
            sensor_cycle(ser, client)

            log_network_info()