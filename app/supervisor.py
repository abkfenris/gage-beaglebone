import logging

import dbus

import pcape


logger = logging.getLogger('gage')


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