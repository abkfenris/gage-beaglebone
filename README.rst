gage-beaglebone
===============

.. image:: https://landscape.io/github/abkfenris/gage-beaglebone/master/landscape.svg?style=flat
   :target: https://landscape.io/github/abkfenris/gage-beaglebone/master
   :alt: Code Health
.. image:: https://requires.io/github/abkfenris/gage-beaglebone/requirements.svg?branch=feature%2Flogger
     :target: https://requires.io/github/abkfenris/gage-beaglebone/requirements/?branch=feature%2Flogger
     :alt: Requirements Status

Collecting stream height via an ultrasonic sensor connected to a BeagleBone Black and communicating it to web server


Environment variables
---------------------



Sensor sampling 
  Environment variables that are used to define valid sampling ranges
  for the sensor, and to make sure the correct sensor is setup.

  - ``GAGE_SERIAL_PORT`` - Serial Port dev path of sensor to sample (default ``'/dev/ttyS2'``)
  - ``GAGE_SERIAL_UART`` - Serial Port UART name of sensor (default ``'UART2'``)
  - ``GAGE_SAMPLE_WAIT`` - Time to wait between collecting each sample (in seconds, default ``5``)
  - ``GAGE_SENSOR_LOW`` - Lowest valid value from the sensor (default ``501`` for using `Maxbotix MB7386`_)
  - ``GAGE_SENSOR_HIGH`` - Highest valid value from the sensor (default ``9998`` for using `Maxbotix MB7386`_)
  - ``GAGE_MIN_SAMPLES``
  - ``GAGE_MAX_ATTEMPTS``
  - ``GAGE_MAX_STD_DEV``


Power control
  Environment variables that control how long the gage is on and off
  as it goes through the day. Mostly used to control the `AndiceLabs Power Cape`_.
  `Power Cape watchdog information`_

  - ``GAGE_POWER_CONSERVE`` - Should the gage shut down and go into power conservation mode between sampling sets
  - ``GAGE_RESTART_TIME``
  - ``GAGE_WATCHDOG_RESET_TIMEOUT``
  - ``GAGE_WATCHDOG_POWER_TIMEOUT``
  - ``GAGE_WATCHDOG_STOP_POWER_TIMEOUT``
  - ``GAGE_WATCHDOG_START_POWER_TIMEOUT``
  - ``GAGE_STARTUP_REASONS``


.. _Maxbotix MB7386: http://maxbotix.com/Ultrasonic_Sensors/MB7386.htm
.. _AndiceLabs Power Cape: http://andicelabs.com/beaglebone-powercape/
.. _Power Cape watchdog information: http://andicelabs.com/2016/05/beaglebone-watchdog-power-cape/