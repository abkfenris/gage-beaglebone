"""
Utility classes
"""
import csv
import os
import signal
import statistics
import subprocess

from app import cell, config, exceptions
from app.log import logger


class TimeoutError(Exception):
    pass


class Timeout(object):

    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_value, traceback):
        signal.alarm(0)


def uptime():
    """
    Return the uptime in seconds (float) since last boot
    """
    with open('/proc/uptime', 'r') as f:
        return float(f.readline().split()[0])


def log_network_info(leds):
    """ Log current network status and toggle LEDs """
    connections = cell.list_active_connections()
    for conn in connections:
        logger.debug(conn)

    if len(connections) > 0:
        leds.led_2 = True  # network connection avaliable
    else:
        leds.led_2 = False


def sd_avaliable():
    """ Returns True if the SD card block device is avaliable to the system """
    output = subprocess.run('fdisk -l', shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return 'mmcblk0' in output.stdout.decode('ASCII')


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


def remove_old_log_files():
    """Removes log files older than MAX_LOG_FILES"""
    ordered = sorted((config.DATA_CSV_FOLDER + filename for filename in os.listdir(config.DATA_CSV_FOLDER)),
                     key=os.path.getctime, reverse=True)
    old = ordered[config.MAX_LOG_FILES:]
    for path in old:
        logger.info(f'Removing log {path} as there are more than MAX_LOG_FILES ({config.MAX_LOG_FILES}).')
        os.remove(path)


def writerow(row, data_csv_path):
    """Write a row to the current csv file"""
    if data_csv_path:
        with open(data_csv_path, 'a') as f:
            writer = csv.writer(f)
            writer.writerow(row)
    else:
        logger.warning(f'DATA_CSV_PATH not avaliable, would have written: {row}')


def clean_sample_mean(sample_func, ser, low, high, min_samples, max_attempts, max_std_dev):
    """With a given sampling_func, sample and discard outliers"""
    samples = [sample_func(ser)]  # initial sample so that stdev doesn't yell at us for too few samples

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
            raise exceptions.TooFewSamples(f'Too few cleaned samples that were not too low ({low})')
        elif high in samples:
            raise exceptions.TooFewSamples(f'Too few cleaned samples that were not too high ({high})')
        else:
            raise exceptions.TooFewSamples('Too few cleaned samples')

    stdev = round(statistics.stdev(cleaned), 2)
    raise exceptions.SamplingError(f'Stdev ({stdev}) did not meet criteria ({max_std_dev}) in {max_attempts}')


def check_config():
    """
    Checks config values to make sure they are reasonable
    """

    # check that register values are not too high
    registers = ((config.RESTART_TIME, 'GAGE_RESTART_TIME'),
                 (config.MIN_VOLTAGE_RESTART_TIME, 'GAGE_MIN_VOLTAGE_RESTART_TIME'),
                 (config.WATCHDOG_RESET_TIMEOUT, 'GAGE_WATCHDOG_RESET_TIMEOUT'),
                 (config.WATCHDOG_POWER_TIMEOUT, 'GAGE_WATCHDOG_POWER_TIMEOUT'),
                 (config.WATCHDOG_STOP_POWER_TIMEOUT, 'GAGE_WATCHDOG_STOP_POWER_TIMEOUT'),
                 (config.WATCHDOG_START_POWER_TIMEOUT, 'GAGE_WATCHDOG_START_POWER_TIMEOUT'))
    for register, register_name in registers:
        if register > 255:
            logger.error(f'{register_name} is set to a value greater than 255 ({register}). '
                         + f'It will instead be interperted as {register % 255}')

    # check that primary sensing period isn't longer than timeout
    sensor_cycle_time = config.WAIT + 5
    if (sensor_cycle_time * config.SAMPLES_PER_RUN) > config.WATCHDOG_STOP_POWER_TIMEOUT:
        logger.error('Aproximate time of main sensor loop ((GAGE_WAIT + sensing time) * GAGE_SAMPLES_PER_RUN)'
                     + ' is greater than GAGE_WATCHDOG_STOP_POWER_TIMEOUT.'
                     + f' ({sensor_cycle_time * config.SAMPLES_PER_RUN} > {config.WATCHDOG_STOP_POWER_TIMEOUT})')

    # check that update check sensing period isn't longer than timeout
    if config.PRE_SHUTDOWN_TIME > config.WATCHDOG_STOP_POWER_TIMEOUT:
        logger.error('Approximate time of update check loop (GAGE_PRE_SHUTDOWN_TIME) is greater than'
                     + ' GAGE_WATCHDOG_STOP_POWER_TIMEOUT.'
                     + f' ({config.PRE_SHUTDOWN_TIME} > {config.GAGE_WATCHDOG_STOP_POWER_TIMEOUT})')
