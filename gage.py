#!/usr/bin/python

import datetime
import time
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

from gage_client.gage_client.client import Client, SendError

import ultrasound
import power
# import pcape

import config


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
        with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
            status_file.write('Successfully sent at {dt} to {url}'.format(
                dt=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                url=destination,
            ))
            status_file.write('  sucess fully uploaded: {success}'.format(
                success=sucessful_ids
            ))
    except Exception as e:
        #sucessful_ids = e.sucessful
        with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
            status_file.write('Send error at {dt} to {url}, {detail}'.format(
                dt=datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
                url=destination,
                detail=e
        #    ))
        #    status_file.write('  failed to upload: {failed}'.format(
        #        failed=e.fail
        #    ))
        #    status_file.write('  sucess fully uploaded: {success}'.format(
        #        success=e.sucessful
        #    ))
#
    # for every id that was sent mark as uploaded
    else:
        sucessful_ids = set(sucessful_ids)
        for sample_id in sucessful_ids:
            sample = Sample.get(Sample.id == sample_id)
            sample.uploaded = True
            sample.save()


if __name__ == '__main__':
    if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
        print 'This program is running as __main__.'
        while True:
            os.system('/gage/powercape/utils/power -s')
            time.sleep(45)
            get_sample()
            time.sleep(15)
            send_samples()
            if not os.path.isfile("/boot/uboot/gagestop"):
                os.system("shutdown -h now")
    else:
        print 'gagestop is in /boot/uboot/ or gagerun is not.'
        exit()
else:
    print 'gage.py is imported'
