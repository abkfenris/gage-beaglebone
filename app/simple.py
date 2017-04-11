import time, datetime, os, logging, subprocess, sys
import serial

import power

PORT = '/dev/ttyS2'
WAIT = int(os.environ.get('GAGE_SIMPLE_WAIT', 5))

class SensorError(Exception):
    pass

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
ch = logging.StreamHandler(sys.stdout)
logger.addHandler(ch)

# enable UART-2 device tree overlay in cape manager
output = subprocess.run(
    ['''sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"'''], 
    stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
if 'I/O error' in output.stderr.decode('utf-8'):
    logger.info('UART-2 already enabled in capemgr')
elif len(output.stderr) > 0:
    logger.error('Other error occured adding UART-2 to capemgr', output)
else:
    logger.info('UART-2 added to capemgr')


ser = serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)

def read_serial():
    for _ in range(50):
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit(): # and data[1:5] != '9999'
                return int(data[1:5])
        logger.debug('Serial returned invalid info, trying again')
    logger.error('Serial did not return valid info in 50 tries')
    raise SensorError

if __name__ == '__main__':
    while True:
        data = read_serial()
        date = datetime.datetime.now()
        volts = power.checkVolts()
        amps = power.checkAmps()
        logger.info(f'{date} {data} {volts} {amps}')
        time.sleep(WAIT)