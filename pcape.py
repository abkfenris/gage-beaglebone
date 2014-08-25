import config
from Adafruit_I2C import Adafruit_I2C

#cycleTime = config.CycleTime

powercapeI2C = Adafruit_I2C(0x21)

def setTime(cycleTime):
	try:
		i2c.write8(7, cycleTime)
	except Exception, e:
		with open('/boot/uboot/gage-status.txt', 'ab') as status_file:
					status_file.write(str(e))