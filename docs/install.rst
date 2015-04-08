Installation
============

After you've  :doc:`built <build>` a gage, it's time to
bring it to life.

Update the distro
-----------------

Initially you should upgrade the distro to the latest Debian release. Follow the
steps from `beagleboard.org`_.

Initial setup
-------------

Continue to follow the initial setup steps from beagleboard.org until you have an
ssh session.

1. Setup a new user
2. Add user to sudoers

Magic - aka Fabric
------------------

Then we use a tool called fabric. If you don't already have it you can
``brew install fabric``, ``sudo apt-get install fabric``, or
``pip install fabric``. For more info see `fabfile.org`_

.. _beagleboard.org: http://beagleboard.org/getting-started
.. _fabfile.org: http://www.fabfile.org/installing.html
