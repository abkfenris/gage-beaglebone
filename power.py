#!/usr/bin/python
# import Adafruit_BBIO.ADC as ADC
import time
import numpy

# ADC.setup()

def checkPower(powerAIN="P9_36"):
	currentPower = ADC.read(powerAIN)*18
	return currentPower
	
	
def powerCheckTrue():
	return "True"
	
def powerCheckMath(powerAIN="P9_36"):
	return "12.4"