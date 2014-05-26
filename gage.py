#!/usr/bin/python

# import gage_config
import config
import ultrasound
# import ephem
from requests import post
import datetime
import power
import time

# print "DepthAIN is " + config.DepthAIN
# print "The depth in cm is " + str(round(ultrasound.checkDepth(6), 2))
# print ""


def send_results():
	level = ultrasound.checkDepth()
	timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S") # remove the microsecond http://stackoverflow.com/questions/7999935/python-datetime-to-string-without-microsecond-component
	battery = power.checkPower()
	payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
	sample = post(config.PostURL, data=payload)
	print timestamp, battery, level
	return True


if __name__ == '__main__':
	while True:
		print 'This program is running as __main__.'
		send_results()
		time.sleep(60)
	else:
		print 'gage.py is imported'