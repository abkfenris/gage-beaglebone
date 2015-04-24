import os

from cell import CellConnection

SPRINT_PATH = os.path.dirname(__file__)


class Sierra250U(CellConnection):
    """
    Context manager to connect to the Sprint Network using a Sierra Wireless
    250U.

    scripts from https://sites.google.com/site/cellularbeaglebone/
    """

    def __enter__(self):
        # find the usb device for the cell modem
        os.system(SPRINT_PATH+'/sierra250u/usb_discover.sh')

        # join the wireless network
        os.system(SPRINT_PATH+'/sierra250u/join_network.sh')

    def __exit__(self, exc_type, exc_value, traceback):
        # Try to turn off ppp
        os.system('/usr/bin/poff')
