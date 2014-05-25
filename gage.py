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
	timestamp = datetime.datetime.now()
	battery = power.checkPower()
	payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
	sample = post(config.PostURL, data=payload)
	print timestamp, battery, level
	return True

while True:
	send_results()
	time.sleep(60)