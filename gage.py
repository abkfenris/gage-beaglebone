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
import os.system

# print "DepthAIN is " + config.DepthAIN
# print "The depth in cm is " + str(round(ultrasound.checkDepth(6), 2))
# print ""


def send_results():
	level = ultrasound.checkDepth()
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # remove the microsecond http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
	battery = power.checkPower()
	payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
	sample = post(config.PostURL, data=payload, auth=(config.Id, config.Password))
	print timestamp, battery, level
	return True


if __name__ == '__main__':
	if os.path.isfile("/boot/uboot/gagerun") and not os.path.isfile("/boot/uboot/gagestop"):
		print 'This program is running as __main__.'		
		while True:
			send_results()
			time.sleep(60)
			os.system("poweroff")
	else:
		print 'gagestop is in /boot/uboot/ or gagerun is not.'
else:
	print 'gage.py is imported'