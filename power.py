#!/usr/bin/python
# import Adafruit_BBIO.ADC as ADC
import time
from ina.Subfact_ina219 import INA219
import numpy

ina = INA219()

def checkPower(j=3):
	
	currentPowerList = [] # create an empty array to store the power values
	
	for i in range(0,j):
		currentPowerList.append(ina.getBusVoltage_V())
		time.sleep(.5) # Take a half second between reading ranges
		
	currentPower = numpy.mean(currentPowerList)
	return currentPower