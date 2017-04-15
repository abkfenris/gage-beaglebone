import os, logging, subprocess, datetime
import requests

from Adafruit_I2C import Adafruit_I2C

RESIN_SUPERVISOR_API_KEY = os.environ.get('RESIN_SUPERVISOR_API_KEY', None)
RESIN_SUPERVISOR_ADDRESS = os.environ.get('RESIN_SUPERVISOR_ADDRESS', None)

powercapeI2C = Adafruit_I2C(0x21, 2)

logger = logging.getLogger('gage')

def set_time(cycle_time):
    """
    Set time in minutes that the PowerCape will wait
    to start the BeagleBone up after shutdown.
    """
    logger.info(f'Setting startup time for {cycle_time} minutes.')
    try:
        powercapeI2C.write8(7, cycle_time)
    except Exception:
        pass


def set_wdt_reset(cycle_time):
    """
    Timeout in seconds before the PowerCape attempts to 
    restart the BeagleBone by sending SYS_RESET
    """
    logger.info(f'Setting watchdog force reset time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(18, cycle_time)
    except Exception:
        pass


def set_wdt_power(cycle_time):
    """
    Timout in seconds before the PowerCape cuts power
    to the BeagleBone
    """
    logger.info(f'Setting watchdog power cuttof time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(19, cycle_time)
    except Exception:
        pass


def set_wdt_stop(cycle_time):
    """
    Timeout in seconds and cut power 
    (for Beaglebones that don't cut power)
    """
    logger.info(f'Setting watchdog power cuttof time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(20, cycle_time)
    except:
        pass


def set_wdt_start(cycle_time):
    """
    Startup timeout in seconds. If I2C activity hasn't been seen on startup
    after this time then it will cycle power on timeout.
    """
    logger.info(f'Setting watchdog startup activity time to {cycle_time} seconds before power cycle.')
    try:
        powercapeI2C.write8(21, cycle_time)
    except:
        pass


def set_startup_reasons(startup_reasons):
    """
    Set startup reason for powercape
    """
    logger.info(f'Setting startup reason {startup_reasons}')
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
    Send resin supervisor shutdown command
    """
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
    logger.info('Setting powercape to cut power in 60 seconds in still running')
    set_wdt_stop(60)

def cape_time():
    """
    Get the current time from the cape as a datetime object
    """
    output = subprocess.run(['/gage/PowerCape/utils/power -r'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True)
    time_str = output.stdout.decode('ASCII').strip()
    return datetime.datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')
