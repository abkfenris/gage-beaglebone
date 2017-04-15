import logging, subprocess

import dbus

from cell import CellConnection, list_connection_ids


logger = logging.getLogger('gage')

class Sierra250U(CellConnection):
    """
    Context manager to connect to the Sprint Network using a Sierra Wireless
    250U.

    scripts from https://sites.google.com/site/cellularbeaglebone/
    """
    def __init__(self):
        output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If the module isn't detected
        if 'Sierra' not in output.stdout.decode('ASCII'):
            # load kernel modules
            output = subprocess.run(['modprobe sierra'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = subprocess.run(['modprobe sierra_net'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            # cycle USB bus
            output = subprocess.run(
                ['sh -c "echo 0 > /sys/bus/usb/devices/1-1/authorized"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = subprocess.run(
                ['sh -c "echo 1 > /sys/bus/usb/devices/1-1/authorized"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if 'Sierra' in output.stdout.decode('ASCII'):
                logger.info('Sierra Cell Modem USB kernel drivers loaded and modem detected')
            else:
                logger.error('Unable to load Sierra Cell Modem kernel drivers')
        else:
            logger.info('Sierra Cell Modem USB kernel drivers already loaded and modem detected')

        uuid = '02d5e625-86a7-448e-8880-91e0977ad4e5'
        nm_id = 'ting-sierra-250u'

        if nm_id not in list_connection_ids():
            logger.info(f'{nm_id} not found in NetworkManager connections. Attempting to add')
            s_con = dbus.Dictionary({
                'type': 'cdma',
                'uuid': uuid,
                'autoconnect': True,
                'id': nm_id})

            s_ipv4 = dbus.Dictionary({
                'method': 'auto'})

            s_serial = dbus.Dictionary({
                'baud': 921600})

            s_cdma = dbus.Dictionary({
                'number': '#777'
            })

            s_ipv6 = dbus.Dictionary({
                'method': 'auto'})

            con = dbus.Dictionary({
                'connection': s_con,
                'cdma': s_cdma,
                'ipv4': s_ipv4,
                #'ipv6': s_ipv6,
                'serial': s_serial})

            bus = dbus.SystemBus()
            proxy = bus.get_object("org.freedesktop.NetworkManager", 
                "/org/freedesktop/NetworkManager/Settings")
            settings = dbus.Interface(proxy, "org.freedesktop.NetworkManager.Settings")
            settings.AddConnection(con)
            if nm_id in list_connection_ids():
                logger.info('Sucessfully added connection for {nm_id}')