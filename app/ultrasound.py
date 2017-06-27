"""
Ultrasonic sensor functions
"""

import logging, subprocess

import serial

import config

logger = logging.getLogger('gage')


def serial_setup():
    """ enable UART-2 device tree overlay in cape manager """
    output = subprocess.run(
        [f'''sh -c "echo 'BB-{config.UART}' > /sys/devices/platform/bone_capemgr/slots"'''], 
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    if 'I/O error' in output.stderr.decode('utf-8'):
        logger.info(f'{config.UART} already enabled in capemgr')
    elif len(output.stderr) > 0:
        logger.error(f'Other error occured adding {UART} to capemgr', output)
    else:
        logger.info(f'{config.UART} added to capemgr')
    ser = serial.Serial(port=config.PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)
    return ser