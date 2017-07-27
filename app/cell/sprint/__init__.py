import logging, subprocess, time

# import dbus
import NetworkManager

from app.cell import CellConnection, list_connection_ids


logger = logging.getLogger('gage')

class Sierra250U(CellConnection):
    """
    Context manager to connect to the Sprint Network using a Sierra Wireless
    250U.

    scripts from https://sites.google.com/site/cellularbeaglebone/
    """
    def __init__(self):
        uuid = '7fb0575b-64f9-4ff0-8820-637b9cbe54b3'
        nm_id = 'ting'

        if nm_id in [conn.Id for conn in NetworkManager.NetworkManager.ActiveConnections]:
            logger.info('ting connection currently active. Leaving it alone')
        else:
            for conn in NetworkManager.Settings.ListConnections():
                if nm_id == conn.GetSettings()['connection']['id']:
                    conn.Delete()
                    logger.info('Deleted old Network Manager connection for ting')
            ting_conn = {
                'connection': {'id': nm_id,
                            'type': 'cdma',
                            'autoconnect': True,
                            'autoconnect-priority': 0,
                            'uuid': uuid},
                'cdma': {'number': '#777'},
                'ppp': {'baud': 460800},
                'ipv4': {'method': 'auto'},
                'ipv6': {'method': 'auto'}
            }
            NetworkManager.Settings.AddConnection(ting_conn)
            logger.info('Added Network Manager connection for ting.')
        

        
        
        output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)

        # If the module isn't detected
        if 'Sierra' not in output.stdout.decode('ASCII'):
            # load kernel modules
            output = subprocess.run(['modprobe sierra'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            output = subprocess.run(['modprobe sierra_net'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)

            time.sleep(1)
            # cycle USB bus
            output = subprocess.run(
                ['sh -c "echo 0 > /sys/bus/usb/devices/1-1/authorized"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
            time.sleep(1)
            output = subprocess.run(
                ['sh -c "echo 1 > /sys/bus/usb/devices/1-1/authorized"'],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True
            )
            time.sleep(5)
            output = subprocess.run(['lsusb'], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            if 'Sierra' in output.stdout.decode('ASCII'):
                logger.info('Sierra Cell Modem USB kernel drivers loaded and USB device detected')
            else:
                logger.error('Unable to load Sierra Cell Modem kernel drivers')
        else:
            logger.info('Sierra Cell Modem USB kernel drivers already loaded and USB device detected')
