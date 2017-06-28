"""
Main script for gage to run. No longer simple.
"""
import datetime
import importlib
import logging
from logging.handlers import RotatingFileHandler
import os
import time

from app.log import formatter, logger, log_levels
from app import config, db, power, pcape, supervisor, ultrasound
from app.gage_client.gage_client import Client
from app.utils import (
    clean_sample_mean,
    log_network_info,
    remove_old_log_files,
    mount_data_sd,
    sd_avaliable,
    writerow,
    uptime
    )
from app.exceptions import SamplingError


def sensor_cycle(ser, client, data_csv_path):
    """Collect and log sensor data once"""
    try:
        distance = clean_sample_mean(ultrasound.read_serial,
                                     ser,
                                     config.SENSOR_LOW,
                                     config.SENSOR_HIGH,
                                     config.MIN_SAMPLES,
                                     config.MAX_ATTEMPTS,
                                     config.MAX_STD_DEV)
        if config.INVERT_SAMPLE:
            distance = config.SENSOR_HIGH - distance
    except SamplingError as error:
        date = datetime.datetime.now()
        logger.error(f'{date} - Sampling error - {error}')
        distance = None
    date = datetime.datetime.now()
    volts = round(power.check_volts(), 2)
    amps = round(power.check_amps(), 2)

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
    writerow((date, distance, 'mm ultrasound', volts, flow, amps), data_csv_path)

    time.sleep(config.WAIT)


if __name__ == '__main__':
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
        file_handler = RotatingFileHandler(config.FILE_LOG_FOLDER + 'syslog', 
                                           maxBytes=10000000, backupCount=config.MAX_LOG_FILES)
        file_handler.setLevel(log_levels.get(config.FILE_LOG_LEVEL, logging.DEBUG))
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

        # Is the stop file present on the SD card
        STOP = os.path.isfile(config.STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            remove_old_log_files()

        data_csv_path = config.DATA_CSV_FOLDER + datetime.date.today().isoformat() + '.csv'

        leds.led_1 = True  # SD Card mounted and avaliable for storage
        db.create_tables([db.Sample], safe=True)
    else:
        logger.error('Micro SD card not avaliable for file storage')
        data_csv_path = False
        STOP = False

    if power.check_volts() < config.MIN_VOLTAGE:
        logger.error(f'System voltage has fallen below minimum voltage specified ({config.MIN_VOLTAGE} V).',
                     f'Shutting down for {config.MIN_VOLTAGE_RESTART_TIME} min to charge.')
        pcape.schedule_restart(config.STARTUP_REASONS, config.MIN_VOLTAGE_RESTART_TIME)
        supervisor.shutdown()

    if uptime() > config.MAX_UPTIME and config.POWER_CONSERVE:
        pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)
        logger.error(f'System has been up for longer than the maximum allowed uptime.',
                     f'({uptime()} > {config.MAX_UPTIME} seconds). Shutting down.')
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
            sensor_cycle(ser, client, data_csv_path)
            log_network_info(leds)

        logger.info(f'Sensing for {config.PRE_SHUTDOWN_TIME} more seconds to allow communication.')
        pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)

        for n in range(config.PRE_SHUTDOWN_TIME // config.WAIT):
            sensor_cycle(ser, client, data_csv_path)

            log_network_info(leds)

        if pcape.update_in_progress():
            remaining_update_wait = config.MAX_UPDATE_WAIT
            for x in range(remaining_update_wait // config.WAIT):
                pcape.set_wdt_power(config.WATCHDOG_STOP_POWER_TIMEOUT)
                logger.info(f'Update in progress: {pcape.update_percentage()}%.',
                            f'Giving it {remaining_update_wait} more seconds.')
                remaining_update_wait -= config.WAIT
                sensor_cycle(ser, client, data_csv_path)
                log_network_info(leds)

                if not pcape.update_in_progress():
                    break
        else:
            logger.debug('No update scheduled, getting ready to shutdown')

        client.send_all()

        STOP = os.path.isfile(config.STORAGE_MOUNT_PATH + '/STOP')

        if not STOP:
            pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)

            logger.debug('Powercape info:')
            for line in pcape.powercape_info():
                logger.debug('   ' + line)

            leds.led_1, leds.led_2 = False, False

            supervisor.shutdown()

    else:
        while True:
            sensor_cycle(ser, client, data_csv_path)
            log_network_info()