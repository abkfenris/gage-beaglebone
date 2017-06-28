"""
Ultrasonic sensor functions
"""

import logging
import subprocess

import serial

from . import config
from . import exceptions

logger = logging.getLogger('gage')


def serial_setup():
    """ enable UART-2 device tree overlay in cape manager """
    output = subprocess.run(
        [f'''sh -c "echo 'BB-{config.UART}' > /sys/devices/platform/bone_capemgr/slots"'''],
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'I/O error' in output.stderr.decode('utf-8'):
        logger.info(f'{config.UART} already enabled in capemgr')
    elif len(output.stderr) > 0:
        logger.error(f'Other error occured adding {config.UART} to capemgr', output)
    else:
        logger.info(f'{config.UART} added to capemgr')
    ser = serial.Serial(port=config.PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)
    return ser


def read_serial(ser):
    """Make 50 attempts to read the sensor serial data. Returns the first valid response"""
    for _ in range(50):
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit():  # and data[1:5] != '9999'
                return int(data[1:5])
        logger.debug('Serial returned invalid info, trying again')
    logger.error('Serial did not return valid info in 50 tries')
    raise exceptions.SensorError
