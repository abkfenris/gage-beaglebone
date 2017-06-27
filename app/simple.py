import time, datetime, os, logging, subprocess, statistics, csv, importlib
import serial
from logging.handlers import RotatingFileHandler

from log import formatter, logger, log_levels
import cell, config, power, pcape, supervisor, ultrasound
from cell import sprint
from gage_client.gage_client import Client
from utils import (
    log_network_info, 
    remove_old_log_files, 
    mount_data_sd, 
    sd_avaliable, 
    uptime
    )
    

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
        distance = clean_sample_mean(ultrasound.read_serial, ser, config.SENSOR_LOW, config.SENSOR_HIGH, config.MIN_SAMPLES, config.MAX_ATTEMPTS, config.MAX_STD_DEV)
        if config.INVERT_SAMPLE:
            distance = config.SENSOR_HIGH - distance
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

    time.sleep(config.WAIT)


if __name__ == '__main__':
    #if POWER_CONSERVE:
    #    pcape.set_wdt_power(WATCHDOG_POWER_TIMEOUT)
    
    pcape.set_system_time()
    pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)
    pcape.set_wdt_start(config.WATCHDOG_START_POWER_TIMEOUT)
    

    leds = pcape.StatusLEDs()
    leds.led_1, leds.led_2 = False, False

    # mount SD and clean out old log files
    SD_CARD = sd_avaliable()
    
    if SD_CARD:
        logger.debug('SD block storage avaliable, attempting to mount')
        mount_data_sd(config.STORAGE_MOUNT_PATH)

        try:
            os.mkdir(config.DATA_CSV_FOLDER)
        except OSError:
            logger.debug(f'Log directory {config.DATA_CSV_FOLDER} already exists')
        else:
            logger.debug(f'Created log directory {config.DATA_CSV_FOLDER}')
        
        try:
            os.mkdir(config.FILE_LOG_FOLDER)
        except OSError:
            logger.debug(f'Syslog directory {config.FILE_LOG_FOLDER} already exists')
        else:
            logger.debug(f'Created syslog directory {config.FILE_LOG_FOLDER}')
        
        # set up file logging
        fh = RotatingFileHandler(config.FILE_LOG_FOLDER + 'syslog', maxBytes=10000000, backupCount=config.MAX_LOG_FILES)
        fh.setLevel(log_levels.get(config.FILE_LOG_LEVEL, logging.DEBUG))
        fh.setFormatter(formatter)
        logger.addHandler(fh)

        # Is the stop file present on the SD card
        STOP = os.path.isfile(config.STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            remove_old_log_files()
        
        DATA_CSV_PATH = config.DATA_CSV_FOLDER + datetime.date.today().isoformat() + '.csv'
        
        leds.led_1 = True # SD Card mounted and avaliable for storage
    else:
        logger.error('Micro SD card not avaliable for file storage')
        DATA_CSV_PATH = False
        STOP = False
    
    if power.checkVolts() < config.MIN_VOLTAGE:
        logger.error(f'System voltage has fallen below minimum voltage specified ({MIN_VOLTAGE} V). Shutting down for {MIN_VOLTAGE_RESTART_TIME} min to charge.')
        
        pcape.set_startup_reasons(config.STARTUP_REASONS)
        pcape.set_cape_time()
        pcape.set_time(config.MIN_VOLTAGE_RESTART_TIME)

        supervisor.shutdown()

    if uptime() > config.MAX_UPTIME and config.POWER_CONSERVE:
        pcape.set_startup_reasons(config.STARTUP_REASONS)
        pcape.set_cape_time()
        pcape.set_time(config.RESTART_TIME)

        logger.error(f'System has been up for longer than the maximum allowed uptime ({uptime()} > {config.MAX_UPTIME} seconds). Shutting down.')

        

        supervisor.shutdown()

    if not config.TESTING_NO_CELL:
        # setup cell
        cell_module_str, cell_method_str = config.CELL_TYPE.rsplit('.', 1)

        cell_module = importlib.import_module(cell_module_str)
        Cell_Modem = getattr(cell_module, cell_method_str)

        cell_modem = Cell_Modem()
    
    # setup serial
    ser = ultrasound.serial_setup()

    # setup client for submission
    client = Client(config.SUBMIT_URL, config.SUBMIT_ID, config.SUBMIT_KEY)

    if config.POWER_CONSERVE and not STOP:
        pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)
        
        for n in range(config.SAMPLES_PER_RUN):
            sensor_cycle(ser, client)
            
            log_network_info(leds)
        
        logger.info(f'Sensing for {config.PRE_SHUTDOWN_TIME} more seconds to allow communication.')
        pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)

        for n in range(config.PRE_SHUTDOWN_TIME // config.WAIT):
            sensor_cycle(ser, client)

            log_network_info(leds)
        
        #pcape.set_time(WATCHDOG_START_POWER_TIMEOUT)

        if pcape.update_in_progress():
            remaining_update_wait = config.MAX_UPDATE_WAIT
            for x in range(remaining_update_wait // config.WAIT):
                pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)
                logger.info(f'Update in progress: {pcape.update_percentage()}%. Giving it {remaining_update_wait} more seconds.')
                remaining_update_wait -= config.WAIT
                sensor_cycle(ser, client)
                
                log_network_info(leds)

                if not pcape.update_in_progress():
                    break
        else:
            logger.debug('No update scheduled, getting ready to shutdown')

        client.send_all()

        STOP = os.path.isfile(config.STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            # set startup reasons
            pcape.set_startup_reasons(config.STARTUP_REASONS)
            pcape.set_cape_time()
            pcape.set_time(config.RESTART_TIME)

            logger.debug('Powercape info:')
            for line in pcape.powercape_info():
                logger.debug('   ' + line)
            
            leds.led_1, leds.led_2 = False, False

            supervisor.shutdown()
    
    else:
        while True:
            sensor_cycle(ser, client)

            log_network_info()