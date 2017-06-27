"""
Utility classes
"""
import signal

import cell

class TimeoutError(Exception):
    pass


class Timeout(object):

    def __init__(self, seconds=1, error_message='Timeout'):
        self.seconds = seconds
        self.error_message = error_message

    def handle_timeout(self, signum, frame):
        raise TimeoutError(self.error_message)

    def __enter__(self):
        signal.signal(signal.SIGALRM, self.handle_timeout)
        signal.alarm(self.seconds)

    def __exit__(self, exc_type, exc_value, traceback):
        signal.alarm(0)


def uptime():
    """
    Return the uptime in seconds (float) since last boot
    """
    with open('/proc/uptime', 'r') as f:
        return float(f.readline().split()[0])


def log_network_info(leds):
    """ Log current network status and toggle LEDs """
    connections = cell.list_active_connections()
    for conn in connections:
        logger.debug(conn)
    
    if len(connections) > 0:
        leds.led_2 = True # network connection avaliable
    else:
        leds.led_2 = False