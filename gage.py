#!/usr/bin/python

# import gage_config
import config
import ultrasound
import ephem
import requests
# import power

print "DepthAIN is " + config.DepthAIN
print "The depth in inches is " + str(round(ultrasound.checkDepth(6), 2))
print ""
