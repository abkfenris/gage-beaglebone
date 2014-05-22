#!/usr/bin/python
import Adafruit_BBIO.ADC as ADC
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.UART as UART
import serial
import time
import numpy
import config

# ADC.setup()
#GPIO.setup(config.DepthGPIO, GPIO.OUT)

ser = serial.Serial()
ser.port = "/dev/ttyO2"
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE

def checkDepth(depthAIN="P9_40",j=3):

	currentDepthList = [] # create an empty array to store the depth values
	
	#GPIO.output(config.DepthGPIO, GPIO.HIGH) # use GPIO to Pin 4 on Ultrasonic sensor to turn ranging on and off (and therefore save power)
	
	time.sleep(.5) # give time for the sensor to wake up and start 
	
	for i in range(0,j):
		ser.open()
		ser.flushOutput()
		ser.flushInput()
		currentDepthList.append(int(ser.read(5)[1:4]))
		ser.close()
		#currentDepthList.append( ADC.read(depthAIN)*1.8/0.00699 ) # *1.8 to get voltage from 0 - 1.8 V, then /0.00699 to get depth and add it to our array
		time.sleep(.5) # Take a half second between reading ranges
		
	#GPIO.output(config.DepthGPIO, GPIO.LOW)
	currentDepth = numpy.mean(currentDepthList)
	return currentDepth

