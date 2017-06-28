
"""
Config from environment information
"""
import os


# Sensor Sampling Environment Variables
PORT = os.environ.get('GAGE_SERIAL_PORT', '/dev/ttyS2')
UART = os.environ.get('GAGE_SERIAL_UART', 'UART2')
STORAGE_MOUNT_PATH = os.environ.get('GAGE_STORAGE_MOUNT_PATH', '/mnt/gagedata')
DATA_CSV_FOLDER = os.environ.get('GAGE_DATA_CSV_FOLDER', STORAGE_MOUNT_PATH + '/logs/')
FILE_LOG_FOLDER = os.environ.get('GAGE_FILE_LOG_FOLDER', STORAGE_MOUNT_PATH + '/syslogs/')
MAX_LOG_FILES = int(os.environ.get('MAX_LOG_FILES', 10))
WAIT = int(os.environ.get('GAGE_SAMPLE_WAIT', 5))
MIN_VOLTAGE = float(os.environ.get('GAGE_MIN_VOLTAGE', 3.0))
CELL_TYPE = os.environ.get('GAGE_CELL_TYPE', 'cell.sprint.Sierra250U')
SAMPLES_PER_RUN = int(os.environ.get('GAGE_SAMPLES_PER_RUN', 10))
PRE_SHUTDOWN_TIME = int(os.environ.get('GAGE_PRE_SHUTDOWN_TIME', 30))
MAX_UPDATE_WAIT = int(os.environ.get('GAGE_MAX_UPDATE_WAIT', 300))
INVERT_SAMPLE = bool(os.environ.get('GAGE_INVERT_SAMPLE', False))

SENSOR_LOW = int(os.environ.get('GAGE_SENSOR_LOW', 501))
SENSOR_HIGH = int(os.environ.get('GAGE_SENSOR_HIGH', 9998))
MIN_SAMPLES = int(os.environ.get('GAGE_MIN_SAMPLES', 10))
MAX_ATTEMPTS = int(os.environ.get('GAGE_MAX_ATTEMPTS', 100))
MAX_STD_DEV = int(os.environ.get('GAGE_MAX_STD_DEV', 100))


# Sample submission server
SUBMIT_ID = int(os.environ.get('GAGE_SUBMIT_ID', False)) or False
SUBMIT_KEY = os.environ.get('GAGE_SUBMIT_KEY')
SUBMIT_URL = os.environ.get('GAGE_SUBMIT_URL')

# Power control Environment Variables
POWER_CONSERVE = bool(os.environ.get('GAGE_POWER_CONSERVE', False))
RESTART_TIME = int(os.environ.get('GAGE_RESTART_TIME', 10))
MIN_VOLTAGE_RESTART_TIME = int(os.environ.get('GAGE_MIN_VOLTAGE_RESTART_TIME', 25))
WATCHDOG_RESET_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_RESET_TIMEOUT', 300))
WATCHDOG_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_POWER_TIMEOUT', 300))
WATCHDOG_STOP_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_STOP_POWER_TIMEOUT', 600))
WATCHDOG_START_POWER_TIMEOUT = int(os.environ.get('GAGE_WATCHDOG_START_POWER_TIMEOUT', 120))
STARTUP_REASONS = os.environ.get('GAGE_STARTUP_REASONS', '0x09')

MAX_UPTIME = int(os.environ.get('GAGE_MAX_UPTIME', WATCHDOG_STOP_POWER_TIMEOUT * 2))

# Logging levels
STDOUT_LOG_LEVEL = os.environ.get('GAGE_STDOUT_LOG_LEVEL', 'WARNING').upper()
FILE_LOG_LEVEL = os.environ.get('GAGE_FILE_LOG_LEVEL', 'INFO').upper()
SENTRY_DSN = os.environ.get('SENTRY_DSN', False)
SENTRY_LOG_LEVEL = os.environ.get('SENTRY_LOG_LEVEL', 'WARNING').upper()


# Testing Environment Variables
TESTING_NO_CELL = os.environ.get('TESTING_NO_CELL')

# Environment Info
RESIN_APP_NAME = os.environ.get('RESIN_APP_NAME')
RESIN_DEVICE_NAME = os.environ.get('RESIN_DEVICE_NAME_AT_INIT')
RESIN_PYTHON_VERSION = os.environ.get('PYTHON_VERSION')
RESIN_SUPERVISOR_VERSION = os.environ.get('RESIN_SUPERVISOR_VERSION')
RESIN_APP_RELEASE = os.environ.get('RESIN_APP_RELEASE')