import time, datetime, os
import serial

PORT = '/dev/ttyS2'

ser = serial.Serial(port=PORT, baudrate=9600, bytesize=8, parity='N', stopbits=1)

def read_serial():
    while True:
        ser.flushInput()
        data = ser.read(5).decode('ASCII')
        if len(data) == 5:
            if data[0] == 'R' and data[1:5].isdigit():
                return int(data[1:5])

while True:
    data = read_serial()
    print(datetime.datetime.now(), data)
    time.sleep(int(os.environ.get('GAGE_SIMPLE_WAIT', 5)))