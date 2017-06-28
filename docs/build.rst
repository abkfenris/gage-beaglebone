Building
========

After you've chosen a site, and figured out if there is cell coverage, and hopefully gotten permission from your local Department Of Transportation, it's time to build a gage for that site.

Parts to acqure
---------------

BeagleBone
~~~~~~~~~~

The core computer controlling the whole system is a BeagleBone.
I've tested a BeagleBone Black, and I believe the BeagleBone Green will work the same, and even be easier to setup (in addition to being less expensive).

- `BeagleBone Black`_ Rev C ($55) or `BeagleBone Green`_ ($39) which comes with other goodies that are helpful like a baseplate that can be screwed or bolted to something.

Communication
~~~~~~~~~~~~~

If you have Sprint coverage, then Ting makes for a reasonable MVNO. 
I've tested with a Sierra 250U modem which is avaliable used for as low as $5.

- `Sierra 250U`_ ($10 - 60)

Storage
~~~~~~~

The BeagleBone uses a µSD card for storage and initial programming.
I'm currently using 16 GB card, which is largely overkill.

- `SanDisk 16 GB Ultra MicroSDHC`_ ($10)


Power Control
~~~~~~~~~~~~~

Rob at AndiceLabs makes an expansion board for the BeagleBone, what is commonly called a cape for power management, including solar charging, starting up on command, and keeping a clock when the board is shut down.

- `Andicelabs 1A Power Cape`_ ($60)
- `Stacking Connectors`_ ($6)


Battery
~~~~~~~

I've tested the gage with the 6.6 Ah battery pack from Adafruit, but it should also work well with a more powerful 1S (3.7 V) battery pack that has a protection circuit.

- `3.7V 6600mAh Lithium Ion Battery Pack`_ ($30) Also can be ordered from AndiceLabs.
- `3.7V 10Ah Lithium Ion Battery Pack`_ ($64)


Solar
~~~~~

Voltaic Systems makes a nice series of solar panels and connectors

- `9 Watt Solar Panel`_ ($79 each) Possibly two panels for shady locations (most).
- `M3511 Splitter`_ ($6) If using two panels.
- `Extension with Exposed Leads`_ ($4) Makes for a nice clean, no outside soldering needed connection.
- `Edge Mounts`_ ($4) Makes it easier to mount two panels side by side.

Case
~~~~
Using a simple water resistant case from Amazon.
Could use something much smaller.

- `Orbit 57095 Sprinkler System Box`_ ($33)


Ultrasonic Sensor
~~~~~~~~~~~~~~~~~
Finally the sensor, which is a `MB7386 Ultrasonic Rangefinder`_ from Maxbotix which will give 10 meters of range and was reccomended by the company after trying others.

- `MB7386 Ultrasonic Rangefinder`_ ($120)
- `MB7950 Mounting Hardware`_ ($3)


Cost Breakdown
--------------

+-------------------------+------+
| Item                    | Cost |
+=========================+======+
| Beaglebone Black        | 55   |
+-------------------------+------+
| Sierra 250u             | 10   |
+-------------------------+------+
| MicroSDHC               | 10   |
+-------------------------+------+
| PowerCape               | 60   |
+-------------------------+------+
| Stacking Headers        | 6    |
+-------------------------+------+
| 3.7V 6600mAh Battery    | 30   |
+-------------------------+------+
| 9 Watt Solar Panel * 2  | 158  |
+-------------------------+------+
| M3511 Splitter          | 6    |
+-------------------------+------+
| Extension               | 4    |
+-------------------------+------+
| Edge Mounts             | 4    |
+-------------------------+------+
| Orbit Sprinkler Box     | 33   |
+-------------------------+------+
| MB7386                  | 120  |
+-------------------------+------+
| Mounting Hardware       | 3    |
+-------------------------+------+
|                         |      |
+-------------------------+------+
| *Total as Tested*:      | 499  |
+-------------------------+------+

Not counting supplies that you can raid from your local hardware store.


.. _BeagleBone Black: https://www.adafruit.com/products/1996
.. _BeagleBone Green: http://www.mouser.com/ProductDetail/Seeed-Studio/102010027/?qs=Hlcjo%2fO3pQ5AxSET1oW%252b%252bg%3d%3d

.. _Sierra 250U: https://www.amazon.com/Sierra-Wireless-Aircard-250U-SW250U3G4G/dp/B00HZTD812/ref=sr_1_6?ie=UTF8&qid=1493134088&sr=8-6&keywords=sierra+250u

.. _9 Watt Solar Panel: https://www.voltaicsystems.com/9-watt-panel
.. _M3511 Splitter: https://www.voltaicsystems.com/m3511-splitter
.. _Extension with Exposed Leads: https://www.voltaicsystems.com/extension-with-exposed-leads
.. _Edge Mounts: https://www.voltaicsystems.com/edge-mounts-2

.. _Orbit 57095 Sprinkler System Box: http://www.amazon.com/gp/product/B000VYGMF2/
.. _SanDisk 16 GB Ultra MicroSDHC: https://www.amazon.com/SanDisk-Ultra-Micro-Adapter-SDSQUNC-016G-GN6MA/dp/B010Q57SEE/ref=sr_1_2?ie=UTF8&qid=1493133490&sr=8-2&keywords=SanDisk+-+Ultra+Plus+16GB+microSDHC+Class+10+UHS-1

.. _3.7V 6600mAh Lithium Ion Battery Pack: https://www.adafruit.com/products/353
.. _3.7V 10Ah Lithium Ion Battery Pack: http://www.batteryspace.com/customizepolymerli-ionbattery37v10ah37wh7aratethinpvcandnolabelcu-mm109pid4816.aspx

.. _Andicelabs 1A Power Cape: http://andicelabs.com/shop/andicelabs/beaglebone-high-power-cape-1a-charge-rate/
.. _Stacking Connectors: http://andicelabs.com/shop/connectors/beaglebone-stacking-headers/

.. _MB7386 Ultrasonic Rangefinder: http://maxbotix.com/Ultrasonic_Sensors/MB7386.htm
.. _MB7950 Mounting Hardware: http://www.maxbotix.com/Ultrasonic_Sensors/MB7950.htm