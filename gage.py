#!/usr/bin/python

# import gage_config
import config
import ultrasound
# import ephem
from requests import post
from requests.auth import HTTPBasicAuth
import datetime
import power
import time
import os.path
import os
from peewee import *

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
	result = CharField()
	serverID = IntegerField()

class Config(BaseModel):
	timing = IntegerField()
	url = CharField()
	
	



def send_results(destination):
	level = ultrasound.checkDepth()
	timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") # remove the microsecond http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
	battery = power.checkPower()
	payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
	try:
		sample = post(config.PostURL, data=payload, auth=(config.Id, config.Password))
	except Exception as detail:
		with open('status.txt', 'ab') as the_file:
			the_file.write(str(detail))
	with open('status.txt', 'ab') as the_file:
		the_file.write(str(payload))
		the_file.write('\n')
	print timestamp, battery, level
	return True


if __name__ == '__main__':
	if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
		print 'This program is running as __main__.'		
		while True:
			time.sleep(60)
			send_results(config.PostURL)
			if not os.path.isfile("/boot/uboot/gagestop"):
				os.system("shutdown -h now")
	else:
		print 'gagestop is in /boot/uboot/ or gagerun is not.'
else:
	print 'gage.py is imported'