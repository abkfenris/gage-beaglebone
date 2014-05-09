#!/usr/bin/python
# import Adafruit_BBIO.ADC as ADC
import time
import numpy

# ADC.setup()

def checkDepth(depthAIN="P9_40",j=3):
	currentDepthList = []
	for i in range(0,j):
		currentDepthList.append( ADC.read(depthAIN)*1.8/0.00699 ) # *1.8 to get voltage from 0 - 1.8 V, then /0.00699 to get depth
		
	currentDepth = numpy.mean(currentDepthList)
	return currentDepth
	
	
def depthCheckTrue():
	return "True"
	
def depthCheckMath(depthAIN="P9_40",j=3):
	currentDepthList =[]
	for i in range(0,j):
		currentDepthList.append(i)
		
	currentDepth = numpy.mean(currentDepthList)
	# print currentDepthList
	return currentDepth