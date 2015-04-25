#!/usr/bin/python

import datetime
import logging
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

import config

logger = logging.getLogger('Rotating Log')
logger.setLevel(config.LOG_LEVEL)

handler = logging.handler.RotatingFileHandler(config.LOG_PATH,
                                              maxBytes=config.LOG_SIZE,
                                              backupCount=config.LOG_BACKUP)

logger.addHandler(handler)

db = SqliteDatabase('/boot/uboot/gage.db')


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


if __name__ == '__main__':
    if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
        print 'This program is running as __main__.'
        os.system('/gage/powercape/utils/power -s')
        if check_time():
            get_sample()
            send_samples()
        else:
            logger.warning('RTC time bad')
            os.system('ntpdate -b -s -u pool.ntp.org')
            os.system('/gage/powercape/util/power -w')
            get_sample()
            send_samples()
        time.sleep(15)
        if not os.path.isfile("/boot/uboot/gagestop"):
            pcape.set_time(int(config.RESTART_TIME))
            os.system("shutdown -h now")
    else:
        print 'gagestop is in /boot/uboot/ or gagerun is not.'
        exit()
else:
    print 'gage.py is imported'
