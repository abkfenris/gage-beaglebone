import os, logging, subprocess, datetime
import requests

from Adafruit_I2C import Adafruit_I2C

RESIN_SUPERVISOR_API_KEY = os.environ.get('RESIN_SUPERVISOR_API_KEY', None)
RESIN_SUPERVISOR_ADDRESS = os.environ.get('RESIN_SUPERVISOR_ADDRESS', None)
POWERCAPE_PATH = '/gage/PowerCape/utils/power'

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
        logger.error('Error setting startup time on PowerCape')


def set_wdt_reset(cycle_time):
    """
    Timeout in seconds before the PowerCape attempts to 
    restart the BeagleBone by sending SYS_RESET
    """
    logger.info(f'Setting watchdog force reset time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(18, cycle_time)
    except Exception:
        logger.error('Error setting restart timeout')


def set_wdt_power(cycle_time):
    """
    Timout in seconds before the PowerCape cuts power
    to the BeagleBone
    """
    logger.info(f'Setting watchdog power cutoff time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(19, cycle_time)
    except Exception:
        logger.error('Error setting watchdog power cutoff timeout')


def set_wdt_stop(cycle_time):
    """
    Timeout in seconds and cut power  (for Beaglebones that 
    don't cut power). Clears on shutdown.
    """
    logger.info(f'Setting watchdog power cuttof time to {cycle_time} seconds.')
    try:
        powercapeI2C.write8(20, cycle_time)
    except:
        logger.error('Error setting watchdog power cut timeout')


def set_wdt_start(cycle_time):
    """
    Startup timeout in seconds. If I2C activity hasn't been seen on startup
    after this time then it will cycle power on timeout.
    """
    logger.info(f'Setting watchdog startup activity time to {cycle_time} seconds before power cycle.')
    try:
        powercapeI2C.write8(21, cycle_time)
    except:
        logger.error('Error setting watchdog startup timeout')


def startup_reasoner(hex_string):
    hex_value = int(hex_string, 16)
    output = []
    if hex_value // 8 == 1:
        output.append('startup timeout completes')
        hex_value -= 8
    if hex_value // 4 == 1:
        output.append('good DC power detected')
        hex_value -= 4
    if hex_value // 2 == 1:
        output.append('external button press')
        hex_value -= 2
    if hex_value // 1 == 1:
        output.append('PowerCape button press')
    return ', '.join(output)

def set_startup_reasons(startup_reasons):
    """
    Set startup reason for powercape
    """
    logger.info(f'Setting startup reason {startup_reasons}  ({startup_reasoner(startup_reasons)})')
    try:
        os.system(f'i2cset -y 2 0x21 4 {startup_reasons}')
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
    output = subprocess.run([POWERCAPE_PATH + ' -r'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True)
    time_str = output.stdout.decode('ASCII').strip()
    return datetime.datetime.strptime(time_str, '%a %b %d %H:%M:%S %Y')


def set_cape_time():
    """
    Set the PowerCape RTC from the system clock
    """
    logger.info('Setting Powercape RTC from system clock')
    output = subprocess.run([POWERCAPE_PATH + ' -w'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)


def set_system_time():
    """
    Set the system time from the PowerCape RTC
    """
    logger.info('Setting system time from PowerCape RTC')
    output = subprocess.run([POWERCAPE_PATH + ' -s'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        shell=True)


def powercape_info():
    """
    Return lines from powercape information
    """
    output = output = subprocess.run([POWERCAPE_PATH + ' -i'], 
        stdout=subprocess.PIPE, 
        stderr=subprocess.PIPE, 
        shell=True)
    
    return output.stdout.decode('ASCII').splitlines()


def update_in_progress():
    """
    Returns true if the resin supervisor is in the process
    of downloading an update
    """
    if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY:
        try:
            res = requests.get(f'{RESIN_SUPERVISOR_ADDRESS}/v1/device?apikey={RESIN_SUPERVISOR_API_KEY}',
                headers={'Content-Type': 'application/json'})
        except requests.exceptions.ConnectionError:
            logger.error('Supervisor offline. Gage most likely does not have a connection')
            return False
        try:
            return res.json()['status'] == 'Downloading' or res.json()['update_pending'] or res.json()['update_downloaded']
        except KeyError:
            logger.error('Unknown response from Resin supervisor')
            return False
        
    else:
        logger.error('RESIN_SUPERVISOR ADDRESS or RESIN_SUPERVISOR_API_KEY not set')
        return False


def update_percentage():
    """
    Returns percent of update downloaded
    """
    if RESIN_SUPERVISOR_ADDRESS and RESIN_SUPERVISOR_API_KEY:
        res = requests.get(f'{RESIN_SUPERVISOR_ADDRESS}/v1/device?apikey={RESIN_SUPERVISOR_API_KEY}',
            headers={'Content-Type': 'application/json'})
        try:
            return res.json()['download_progress']
        except KeyError:
            logger.error('Unknown response from Resin supervisor')
    else:
        logger.error('RESIN_SUPERVISOR ADDRESS or RESIN_SUPERVISOR_API_KEY not set')


class StatusLEDs(object):
    """Lets you change the Powercape LEDs for showing board status"""
    def __init__(self):
        self.initial_register_value = powercapeI2C.readU8(3)
        self._led_1 = False
        self._led_2 = False
    
    def set_leds(self):
        """Sets the LEDS to be illuminated or not and preserves the origional value"""
        value = self.initial_register_value + self._led_1 * 2 + self._led_2 * 4
        powercapeI2C.write8(3, value)

    @property
    def led_1(self):
        return self._led_1

    @led_1.setter
    def led_1(self, value):
        """ Set to True to toggle LED 1 on """
        self._led_1 = value
        self.set_leds()
    
    @property
    def led_2(self):
        return self._led_2
    
    @led_2.setter
    def led_2(self, value):
        """ Set to True to toggle LED 2 on """
        self._led_2 = value
        self.set_leds()