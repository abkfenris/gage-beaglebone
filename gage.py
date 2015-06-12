#!/usr/bin/python

import Adafruit_BBIO.GPIO as GPIO
import datetime
import logging
from logging.handlers import RotatingFileHandler
import os.path
import os
from peewee import (SqliteDatabase,
                    Model,
                    DateTimeField,
                    FloatField,
                    BooleanField,
                    TextField,
                    IntegerField,
                    CharField)
import time

from gage_client.gage_client.client import Client, SendError

import ultrasound
import pcape
import power
from utils import Timeout, TimeoutError

import config

logger = logging.getLogger('Rotating Log')
logger.setLevel(config.LOG_LEVEL)

handler = RotatingFileHandler(config.LOG_PATH,
                              maxBytes=config.LOG_SIZE,
                              backupCount=config.LOG_BACKUP)

logger.addHandler(handler)

db = SqliteDatabase('/boot/uboot/gage.db')

GPIO.setup('P8_12', GPIO.IN)


class BaseModel(Model):
    class Meta:
        database = db


class Sample(BaseModel):
    timestamp = DateTimeField()
    level = FloatField()
    volts = FloatField()
    amps = FloatField()
    uploaded = BooleanField()
    result = TextField(null=True)


class Config(BaseModel):
    timing = IntegerField()
    url = CharField()


def get_sample():
    level = ultrasound.checkDepth()
    # remove the microsecond
    # http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
    timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")
    volts = power.checkVolts()
    amps = power.checkAmps()
    new_sample = Sample.create(timestamp=timestamp,
                               level=level,
                               volts=volts,
                               amps=amps,
                               uploaded=False)


def send_samples(destination=config.PostURL,
                 gage_id=config.Id,
                 password=config.Password):

    # set up client
    client = Client(destination, gage_id, password)

    # get samples that need to be sent and add to readings queue
    for sample in Sample.select().where(Sample.uploaded == False):
        client.reading('level', str(sample.timestamp), sample.level, id=sample.id)
        client.reading('volts', str(sample.timestamp), sample.volts, id=sample.id)
        client.reading('amps', str(sample.timestamp), sample.amps, id=sample.id)

    # try to send and write result to status file
    try:
        result, sucessful_ids = client.send_all()
        logger.info('Successfully sent at {dt} to {url}'.format(
            dt=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            url=destination,
        ))
        logger.info('  ids uploaded: {success}'.format(success=sucessful_ids))
    except Exception as e:
        logger.warning('Send error at {dt} to {url}, {detail}'.format(
            dt=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            url=destination,
            detail=e
        ))
    # for every id that was sent mark as uploaded
    else:
        sucessful_ids = set(sucessful_ids)
        for sample_id in sucessful_ids:
            sample = Sample.get(Sample.id == sample_id)
            sample.uploaded = True
            sample.save()


def check_time():
    """
    Compare current time to last time in database
    """
    sample = Sample.select().order_by(Sample.timestamp.desc()).get()
    return datetime.datetime.utcnow() > sample.timestamp


def check_switch():
    """
    Returns True if GPIO P8_12 is brought to 3.3 V (connected to P9_03)
    """
    if GPIO.input('P8_12') is 1:
        return True
    return False


if __name__ == '__main__':
    if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
        print 'This program is running as __main__.'
        os.system('/gage/powercape/utils/power -s')
        pcape.set_startup_reasons(config.STARTUP_REASONS)
        pcape.set_wdt_start(300)
        # set SYS_RESET timeout
        pcape.set_wdt_stop(300)
        try:
            with Timeout(60):
                if check_time():
                    #with config.Cell():
                    get_sample()
                    send_samples()
                else:
                    logger.warning('RTC time bad')
                    #with config.Cell():
                    os.system('ntpdate -b -s -u pool.ntp.org')
                    os.system('/gage/powercape/util/power -w')
                    get_sample()
                    send_samples()
        except TimeoutError as e:
            logger.warning('TimeoutError: {e}'.format(e=e))
        time.sleep(15)
        if not os.path.isfile("/boot/uboot/gagestop") or not check_switch():
            pcape.set_time(int(config.RESTART_TIME))
            pcape.set_wdt_stop(60)
            # set WDT stop timeout incase the power isn't cut
            os.system("shutdown -h now")
    else:
        print 'gagestop is in /boot/uboot/ or gagerun is not.'
        pcape.set_wdt
        exit()
else:
    print 'gage.py is imported'
