import os
import time

import netifaces

from cell import CellConnection
from utils import TimeoutError

SPRINT_PATH = os.path.dirname(__file__)


class Sierra250U(CellConnection):
    """
    Context manager to connect to the Sprint Network using a Sierra Wireless
    250U.

    scripts from https://sites.google.com/site/cellularbeaglebone/
    """

    def __enter__(self):
        # find the usb device for the cell modem
        os.system('ifup ppp0')
        for x in range(10):
            if 'ppp0' in netifaces.interfaces():
                break
            time.sleep(6)
        else:
            raise TimeoutError('Unable to dial a cell connection')

    def __exit__(self, exc_type, exc_value, traceback):
        # Try to turn off ppp
        os.system('ifdown ppp0')

    def install(self):
        """
        Install the required goodies using fabric
        """
        from fabric.api import cd
        from fabric.contrib.files import append
        from fabtools import require
        with cd('/etc'):
            require.file('wvdial.conf',
                         source='cell/sprint/sierra250u/config_files/wvdial.conf',
                         use_sudo=True)
        append('/etc/network/interfaces',
               'iface ppp0 inet wvdial',
               use_sudo=True)
