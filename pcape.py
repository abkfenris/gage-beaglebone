import config
from Adafruit_I2C import Adafruit_I2C

#cycleTime = config.CycleTime

powercapeI2C = Adafruit_I2C(0x21)

def setTime(cycleTime):
	try:
		powercapeI2C.write8(7, cycleTime)
	except Exception, e:
		pass