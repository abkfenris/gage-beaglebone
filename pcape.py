from Adafruit_I2C import Adafruit_I2C

powercapeI2C = Adafruit_I2C(0x21)


def set_time(cycle_time):
    """
    Set time till restart
    """
    try:
        powercapeI2C.write8(7, cycle_time)
    except Exception:
        pass


def set_wdt_reset(cycle_time):
    """
    Timeout in seconds and send SYS_RESET
    """
    try:
        powercapeI2C.write8(18, cycle_time)
    except Exception:
        pass


def set_wdt_power(cycle_time):
    """
    Timout in seconds and cut power
    """
    try:
        powercapeI2C.write8(19, cycle_time)
    except Exception:
        pass


def set_wdt_stop(cycle_time):
    """
    Timeout in seconds and cut power (for Beaglebones that don't cut power)
    """
    try:
        powercapeI2C.write8(20, cycle_time)
    except:
        pass


def set_wdt_start(cycle_time):
    """
    Startup timeout in seconds. If I2C activity hasn't been seen on startup
    after this time then it will cycle power on timeout.
    """
    try:
        powercapeI2C.write8(21, cycle_time)
    except:
        pass


def set_startup_reasons(startup_reasons):
    """
    Set startup reason for powercape
    """
    try:
        powercapeI2C.write16(startup_reasons)
    except:
        pass
