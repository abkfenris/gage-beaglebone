import time, datetime, os, logging, subprocess
import serial

PORT = '/dev/ttyS2'
WAIT = int(os.environ.get('GAGE_SIMPLE_WAIT', 5))

logger = logging.getLogger(__name__)


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
    while True: # for _ in range(60) ?
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit(): # and data[1:5] != '9999'
                return int(data[1:5])

while True:
    data = read_serial()
    print(datetime.datetime.now(), data)
    time.sleep(WAIT)