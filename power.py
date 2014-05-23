#!/usr/bin/python
# import Adafruit_BBIO.ADC as ADC
import time
from ina.Subfact_ina219 import INA219
import numpy

ina = INA219()

def checkPower(j=3):
	
	currentPowerList = [] # create an empty array to store the power values

	#for i in range(0,j):
	#	ser.open()
	#	ser.flushOutput()
	#	ser.flushInput()
	#	currentDepthList.append(int(ser.read(5)[1:4]))
	#	ser.close()

	#	time.sleep(.5) # Take a half second between reading ranges
		
	#currentDepth = numpy.mean(currentDepthList)
	
	currentPower.append(ina.getBusVoltage_V()
	return currentPower