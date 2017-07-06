import logging
import os

import dbus
import requests
from app import pcape

logger = logging.getLogger('gage')

RESIN_SUPERVISOR_API_KEY = os.environ.get('RESIN_SUPERVISOR_API_KEY', None)
RESIN_SUPERVISOR_ADDRESS = os.environ.get('RESIN_SUPERVISOR_ADDRESS', None)


def shutdown():
    """
    Uses dbus to shutdown, and sets a 60 second timeout on powercape to make sure
    """
    logger.debug('Shutting down using dbus')
    pcape.set_wdt_stop(60)

    bus = dbus.SystemBus()
    bus_object = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    bus_object.PowerOff(dbus_interface='org.freedesktop.systemd1.Manager')


def reboot():
    """
    Uses dbus to restart
    """
    logger.debug('Using dbus to restart')

    bus = dbus.SystemBus()
    bus_object = bus.get_object('org.freedesktop.systemd1', '/org/freedesktop/systemd1')
    bus_object.Reboot(dbus_interface='org.freedesktop.systemd1.Manager')


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
            return (res.json()['status'] == 'Downloading'
                    or res.json()['update_pending']
                    or res.json()['update_downloaded'])
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


def toggle_update_check():
    """
    Tells the supervisor to check for an update
    """
    if RESIN_SUPERVISOR_ADDRESS:
        requests.post(f'{RESIN_SUPERVISOR_ADDRESS}/v1/update?apikey={RESIN_SUPERVISOR_API_KEY}',
                      headers={'Content-Type': 'application/json'})
    else:
        logger.error('RESIN_SUPERVISOR ADDRESS or RESIN_SUPERVISOR_API_KEY not set')