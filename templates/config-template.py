Name = '{{ name }}'  # Friendly name for the gage
Id = '{{ id_num }}'  # Gage ID number on server
Password = '{{ secret_key }}'  # Password for uploading data to server
DepthAIN = '{{ depth_ain }}'  # AIN that the ultrasonic sensor
DepthGPIO = '{{ depth_gpio }}'  # GPIO for ultrasonic sensor
DepthUART = '{{ uart }}'  # UART for ultrasonic sensor
SerialDev = '{{ serial_dev }}'  # TTY for ultrasonic sensor
PostURL = '{{ url }}'  # URL for server API endpoint
RESTART_TIME = '{{ restart_time }}'  # Downtime between cycles
CELL_TIMEOUT = {{ cell_timeout }}  # how many seconds to wait to timeout cell
from {{ cell_base }} import {{ cell_import }} as Cell
import logging
LOG_LEVEL = logging.INFO
LOG_PATH = '/boot/uboot/gage-status.txt'
LOG_SIZE = 2000000
LOG_BACKUP = 5
