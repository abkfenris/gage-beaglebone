#!/usr/bin/python
import Adafruit_BBIO.GPIO as GPIO
import Adafruit_BBIO.UART as UART
import serial # aka pyserial
import time
import numpy
import config

UART.setup(config.DepthUART)

#GPIO.setup(config.DepthGPIO, GPIO.OUT)

ser = serial.Serial()
ser.port = config.SerialDev
ser.baudrate = 9600
ser.bytesize = serial.EIGHTBITS
ser.parity = serial.PARITY_NONE
ser.stopbits = serial.STOPBITS_ONE

def checkDepth(j=3):

	currentDepthList = [] # create an empty array to store the depth values
	
	#GPIO.output(config.DepthGPIO, GPIO.HIGH) # use GPIO to Pin 4 on Ultrasonic sensor to turn ranging on and off (and therefore save power)
	
	time.sleep(.5) # give time for the sensor to wake up and start 
	
	for i in range(0,j):
		ser.open()
		ser.flushOutput()
		ser.flushInput()
		try:
			currentDepthList.append(int(ser.read(5)[1:4]))
		except ValueError:
			ser.flushInput()
		ser.close()

		time.sleep(.5) # Take a half second between reading ranges
		
	#GPIO.output(config.DepthGPIO, GPIO.LOW)
	currentDepth = numpy.mean(currentDepthList)
	return currentDepth

