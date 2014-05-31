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
	result = TextField(null=True)
	server_sample_id = IntegerField(null=True)

class Config(BaseModel):
	timing = IntegerField()
	url = CharField()

def get_sample():
	level = ultrasound.checkDepth()
	timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") # remove the microsecond http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
	volts = power.checkVolts()
	amps = power.checkAmps()
	new_sample = Sample.create(timestamp=timestamp, level=level, volts=volts, amps=amps, uploaded=False)



def send_samples(destination=config.PostURL,id=config.Id,password=config.Password):
	for sample in Sample.select().where(Sample.uploaded == False).order_by(Sample.timestamp.asc()):
		payload = {'level': sample.level, 'battery': sample.volts, 'timestamp': str(sample.timestamp)}
		try:
			submit_sample = post(config.PostURL, data=payload, auth=(config.Id, config.Password), timeout=10)
		except Exception as detail:
			sample.result = detail
			sample.uploaded = False
			sample.save()
			with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
				status_file.write('Failed upload at ')
				status_file.write(str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
				status_file.write(' ')
				status_file.write(str(detail))
				status_file.write(' ')
		else:
			if submit_sample.status_code == 201:
				sample.uploaded = True
				data = submit_sample.json()
				sample.result = data
				try:
					sample.server_sample_id = data['server_sample_id']
				except:
					pass
				if 'Access' in data:
					with open('/boot/uboot/gagestop', 'a') as stop_file:
						stop_file.write('Stopped at ')
						stop_file.write(str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
				sample.save()
				with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
					status_file.write('Sample uploaded at ')
					status_file.write(str(datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")))
					status_file.write(' ')
					status_file.write(str(submit_sample.json()))
					status_file.write(' ')
		with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
			status_file.write(str(payload))
			status_file.write('\n')
	return True
		


#	level = ultrasound.checkDepth()
#	timestamp = datetime.datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S") # remove the microsecond http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
#	battery = power.checkPower()
#	payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
#	try:
#		sample = post(config.PostURL, data=payload, auth=(config.Id, config.Password))
#	except Exception as detail:
#		with open('\boot\uboot\status.txt', 'ab') as the_file:
#			the_file.write(str(detail))
#	with open('\boot\uboot\status.txt', 'ab') as the_file:
#		the_file.write(str(payload))
#		the_file.write('\n')
#	print timestamp, battery, level
#	return True


if __name__ == '__main__':
	if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
		print 'This program is running as __main__.'		
		while True:
			time.sleep(15)
			get_sample()
			time.sleep(45)
			send_samples()
			if not os.path.isfile("/boot/uboot/gagestop"):
				os.system("shutdown -h now")
	else:
		print 'gagestop is in /boot/uboot/ or gagerun is not.'
		exit()
else:
	print 'gage.py is imported'