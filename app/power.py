#!/usr/bin/python

import time, statistics, subprocess

SLEEP_TIME = .01
PATH = '/gage/PowerCape/utils/ina219'

def checkPower(j=3):
    """
    Really a dupe of checkVolts
    """

    currentPowerList = []  # create an empty array to store the power values

    for i in range(0, j):
        currentPowerList.append(ina.getBusVoltage_V())
        time.sleep(SLEEP_TIME)

    currentPower = statistics.mean(currentPowerList)
    return currentPower


def checkVolts(j=3):
    """
    Return the current bus voltage (Battery Voltage)
    """
    currentVoltsList = []
    for i in range(0, j):
        volts_process = subprocess.run([PATH, '-v'],
                                       stdout=subprocess.PIPE, 
                                       stderr=subprocess.PIPE)
        volts = float(volts_process.stdout.decode('utf-8').strip()) / 1000
        currentVoltsList.append(volts)
        time.sleep(SLEEP_TIME)

    currentVolts = statistics.mean(currentVoltsList)
    return currentVolts


def checkAmps(j=3):
    """
    Return the current bus miliamphrage
    Positive is discharging the battery, negative is chargine
    """
    currentAmpsList = []
    for i in range(0, j):
        
        amps_process = subprocess.run([PATH, '-c'],
                                      stdout=subprocess.PIPE,
                                      stderr=subprocess.PIPE)
        amps = float(amps_process.stdout.decode('utf-8').strip())
        currentAmpsList.append(amps)
        time.sleep(SLEEP_TIME)

    currentAmps = statistics.mean(currentAmpsList)
    return currentAmps
