#!/usr/bin/python

# import gage_config
import config
import ultrasound
# import ephem
from requests import post
import datetime
import power

# print "DepthAIN is " + config.DepthAIN
# print "The depth in cm is " + str(round(ultrasound.checkDepth(6), 2))
# print ""

level = ultrasound.checkDepth()
timestamp = datetime.datetime.now()
battery = power.checkPower()
payload = {'level': level, 'battery': battery, 'timestamp': timestamp}
sample = post(config.PostURL, data=payload)