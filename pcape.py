from Adafruit_I2C import Adafruit_I2C

powercapeI2C = Adafruit_I2C(0x21)


def set_time(cycle_time):
    try:
        powercapeI2C.write8(7, cycle_time)
    except Exception:
        pass
