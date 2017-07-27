"""
Main script for gage to run. No longer simple.
"""
import os
import sys
import time

from app.log import logger


def log_uncaught_exceptions(exc_type, exc_value, tb):
    try:
        sleep_time = int(os.environ.get('GAGE_EXCEPTION_SLEEP'))
    except (TypeError, ValueError):
        sleep_time = 60
    logger.critical(f'Uncaught exception, sleeping for {sleep_time} to allow updates',
                    exc_info=(exc_type, exc_value, tb))

    # give the app a chance to update
    try:
        from app import config, supervisor, pcape
    except ImportError as e:
        logger.warning(f'Unable to import in uncaught exceptions: {e}')
    else:
        supervisor.toggle_update_check()
        pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)
        pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)
        pcape.log_powercape_info()

    time.sleep(sleep_time)

    if supervisor.update_in_progress():
        pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)
        logger.info(f'Waiting for another {config.MAX_UPDATE_WAIT} seconds for an update')
        time.sleep(config.MAX_UPDATE_WAIT)
    

    pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)
    pcape.log_powercape_info()

    supervisor.shutdown()


sys.excepthook = log_uncaught_exceptions


import datetime  # noqa: E402
import importlib  # noqa: E402
import logging  # noqa: E402
from logging.handlers import RotatingFileHandler  # noqa: E402

from app import config, pcape, power, supervisor, ultrasound  # noqa: E402
from app.exceptions import SamplingError  # noqa: E402
from app.gage_client.gage_client import Client  # noqa: E402
from app.gage_client.gage_client.client import SendError  # noqa: E402
from app.log import formatter, log_levels  # noqa: E402
from app.utils import (clean_sample_mean, log_network_info, mount_data_sd,
                       remove_old_log_files, sd_avaliable, uptime, writerow, check_config)  # noqa: E402


def sensor_cycle(ser, sample, data_csv_path):
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
        sample.create(
            timestamp=date,
            level=distance,
            volts=volts,
            amps=amps,
            uploaded=False)

    if amps < 0:
        flow = 'charging'
    elif amps < 2:
        flow = 'float'
    else:
        flow = 'discharging'

    logger.info(f'{distance}mm {volts}v {flow} {amps}ma')
    writerow((date, distance, 'mm ultrasound', volts, flow, amps), data_csv_path)

    time.sleep(config.WAIT)


def send_samples(Sample, submit_url=config.SUBMIT_URL, submit_id=config.SUBMIT_ID, submit_key=config.SUBMIT_KEY):
    samples = [sample for sample in Sample.select().where(Sample.uploaded == False)]
    
    chunk_size = 10

    sample_chunks = [samples[i:i + chunk_size] for i in range(0, len(samples), chunk_size)]

    for chunk in sample_chunks:
        client = Client(submit_url, submit_id, submit_key)
        # Intentionally broken client
        # client = Client(submit_url, submit_id, submit_id)
        for sample in chunk:
            timestamp = str(sample.timestamp)
            client.reading('level', timestamp, sample.level, id=sample.primary_key)
            client.reading('volts', timestamp, sample.volts, id=sample.primary_key)
            client.reading('amps', timestamp, sample.amps, id=sample.primary_key)
        try:
            result, successful_ids = client.send_all()
        except SendError as e:
            logger.warning(f'Send error to {submit_url}: {e}', exc_info=e)
        else:
            logger.info(f'Successfully sent at to {submit_url}')
            successful_ids = set(successful_ids)
            logger.debug(f'Sucessful ids ({successful_ids})')
            query = Sample.update(uploaded=True).where(Sample.primary_key.in_(successful_ids))
            query.execute()


def main():
    """
    Run the main stuff
    """
    pcape.set_system_time()
    pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)
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

        from app.db import db, Sample

        db.connect()
        db.create_tables([Sample], safe=True)
    else:
        logger.error('Micro SD card not avaliable for file storage')
        data_csv_path = False
        STOP = False
    
    check_config()

    # shutdown quickly if the power is too low
    if power.check_volts() < config.MIN_VOLTAGE:
        logger.error(f'System voltage has fallen below minimum voltage specified ({config.MIN_VOLTAGE} V).',
                     f'Shutting down for {config.MIN_VOLTAGE_RESTART_TIME} min to charge.')
        pcape.schedule_restart(config.STARTUP_REASONS, config.MIN_VOLTAGE_RESTART_TIME)
        supervisor.shutdown()

    # if the system has been awake too long (due to crashing container or otherwise)
    # shutdown quickly
    if uptime() > config.MAX_UPTIME and config.POWER_CONSERVE:
        pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)
        current_uptime = uptime()
        logger.error('System has been up for longer than the maximum allowed uptime.'
                     + f' ({current_uptime} > {config.MAX_UPTIME} seconds). Shutting down.')
        supervisor.shutdown()
    
    pcape.log_powercape_info()

    # setup cell modem unless in testing mode
    if not config.TESTING_NO_CELL:
        # setup cell
        cell_module_str, cell_method_str = config.CELL_TYPE.rsplit('.', 1)

        cell_module = importlib.import_module(cell_module_str)
        Cell_Modem = getattr(cell_module, cell_method_str)

        cell_modem = Cell_Modem()

    # setup serial
    ser = ultrasound.serial_setup()

    # If the stop file is not found, and the gage is in power conserve (normal) mode
    if config.POWER_CONSERVE and not STOP:
        pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)

        # Primary sensing period
        for n in range(config.SAMPLES_PER_RUN):
            sensor_cycle(ser, Sample, data_csv_path)
            log_network_info(leds)

        logger.info(f'Sensing for {config.PRE_SHUTDOWN_TIME} more seconds to allow communication.')
        pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)

        # Update check sensing period
        for n in range(config.PRE_SHUTDOWN_TIME // config.WAIT):
            sensor_cycle(ser, Sample, data_csv_path)
            log_network_info(leds)

        # Download and apply updates if avaliable
        if supervisor.update_in_progress():
            remaining_update_wait = config.MAX_UPDATE_WAIT
            for x in range(remaining_update_wait // config.WAIT):
                pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)
                update_percentage = supervisor.update_percentage()
                logger.info(f'Update in progress: {update_percentage}%.'
                            + f' Giving it {remaining_update_wait} more seconds.')
                remaining_update_wait -= config.WAIT
                sensor_cycle(ser, Sample, data_csv_path)
                log_network_info(leds)

                if not supervisor.update_in_progress():
                    break
        else:
            logger.debug('No update scheduled, getting ready to shutdown')

        pcape.set_wdt_stop(config.WATCHDOG_STOP_POWER_TIMEOUT)
        send_samples(Sample)

        STOP = os.path.isfile(config.STORAGE_MOUNT_PATH + '/STOP')  # NOQA: N806

        if not STOP:
            pcape.schedule_restart(config.STARTUP_REASONS, config.RESTART_TIME)

            pcape.log_powercape_info()

            leds.led_1, leds.led_2 = False, False

            supervisor.shutdown()

    else:
        while True:
            sensor_cycle(ser, Sample, data_csv_path)
            log_network_info(leds)

if __name__ == '__main__':
    main()
