import os
import requests
import os
import logging

from Adafruit_I2C import Adafruit_I2C

RESIN_SUPERVISOR_API_KEY = os.environ.get('RESIN_SUPERVISOR_API_KEY', None)
RESIN_SUPERVISOR_ADDRESS = os.environ.get('RESIN_SUPERVISOR_ADDRESS', None)

powercapeI2C = Adafruit_I2C(0x21, 2)

logger = logging.getLogger(__name__)

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
        os.system('i2cset -y 2 0x21 4 {startup_reasons}'.format(startup_reasons=startup_reasons))
    except:
        pass


def reboot():
    """
    Send resin supervisor reboot command
    """
    if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY:
        res = requests.post(
            f'{RESIN_SUPERVISOR_ADDRESS}/v1/reboot?apikey={RESIN_SUPERVISOR_API_KEY}', 
            headers={'Content-Type': 'application/json'})
        try:
            if res.json()['Data'] != 'OK':
                logger.error(f'Resin supervisor did not respond with "Data":"OK" Response was: {res.json()}')
            else:
                logger.debug('Resin supervisor responded "OK" to reboot request')
        except KeyError:
            logger.error('No "Data" key in Resin supervisor response.')
    else:
        logger.error('RESIN_SUPERVISOR_ADDRESS or RESIN_SUPERVISOR_API_KEY not in environment')
    logger.info('Setting powercape to cut power in 60 seconds if still running')
    set_wdt_stop(60) # cut power in 60 seconds if still running.

def shutdown():
    """
    Send resin supervisor shutdown command"""
    if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY:
        res = requests.post(
            f'{RESIN_SUPERVISOR_ADDRESS}/v1/shutdown?apikey={RESIN_SUPERVISOR_API_KEY}',
            headers={'Content-Type': 'application/json'})
        try:
            if res.json()['Data'] != 'OK':
                logger.error(f'Resin supervisor did not respond with "DATA":"OK". Response was: {res.json()}')
            else:
                logger.debug('Resin supervisor responded "OK" to reboot request')
        except KeyError:
            logger.error('No "DATA" key in Resin supervisor response')
    else:
        logger.error('RESIN_SUPERVISOR_ADDRESS or RESIN_SUPERVISOR_API_KEY not in environment')
    logger.info('Setting pwoercape to cut power in 60 seconds in still running')
    set_wdt_stop(60)