"""
Functions for reading power usage
"""
import time
import statistics
import subprocess

SLEEP_TIME = .01
PATH = '/gage/PowerCape/utils/ina219'


def check_power(j=3):
    """
    Really a dupe of checkVolts
    """
    current_power = []  # create an empty array to store the power values

    for i in range(0, j):
        current_power.append(ina.getBusVoltage_V())
        time.sleep(SLEEP_TIME)

    current_power = statistics.mean(current_power)
    return current_power


def check_volts(j=3):
    """
    Return the current bus voltage (Battery Voltage)
    """
    current_volts = []
    for i in range(0, j):
        volts_process = subprocess.run([PATH, '-v'],
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
        volts = float(volts_process.stdout.decode('utf-8').strip()) / 1000
        current_volts.append(volts)
        time.sleep(SLEEP_TIME)

    current_volts = statistics.mean(current_volts)
    return current_volts


def check_amps(j=3):
    """
    Return the current bus miliamphrage
    Positive is discharging the battery, negative is chargine
    """
    current_amps = []
    for i in range(0, j):

        amps_process = subprocess.run([PATH, '-c'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        amps = float(amps_process.stdout.decode('utf-8').strip())
        current_amps.append(amps)
        time.sleep(SLEEP_TIME)

    current_amps = statistics.mean(current_amps)
    return current_amps
