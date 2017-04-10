#!/usr/bin/python
# import Adafruit_BBIO.ADC as ADC
import time
from ina.Subfact_ina219 import INA219
import statistics

ina = INA219()


def checkPower(j=3):
    """
    Really a dupe of checkVolts
    """

    currentPowerList = []  # create an empty array to store the power values

    for i in range(0, j):
        currentPowerList.append(ina.getBusVoltage_V())
        time.sleep(.5)  # Take a half second between reading ranges

    currentPower = statistics.mean(currentPowerList)
    return currentPower


def checkVolts(j=3):
    """
    Return the current bus voltage (Battery Voltage)
    """
    currentVoltsList = []
    for i in range(0, j):
        currentVoltsList.append(ina.getBusVoltage_V())
        time.sleep(.5)

    currentVolts = statistics.mean(currentVoltsList)
    return currentVolts


def checkAmps(j=3):
    """
    Return the current bus miliamphrage
    Positive is discharging the battery, negative is chargine
    """
    currentAmpsList = []
    for i in range(0, j):
        currentAmpsList.append(ina.getCurrent_mA())
        time.sleep(.5)

    currentAmps = statistics.mean(currentAmpsList)
    return currentAmps
