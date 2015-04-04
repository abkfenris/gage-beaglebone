"""
Fabric commands to setup beaglebone
"""
from fabric.api import cd, env, lcd, put, prompt, local, sudo, prefix
from fabric.contrib.files import exists
from fabric.contrib.console import confirm
from fabtools import require

try:
    from fabhosts import bone
except ImportError:
    pass

gage_folder = '/gage'
time_till_startup = '14'
time_till_watchdog = ''
startup_reasons = '0x09'

# startup_reasons:
# 0x01 START_BUTTON
# 0x02 START_EXTERNAL
# 0x04 START_PWRGOOD
# 0x08 START_TIMEOUT
# 0x0F START_ALL
# Most likely we want to use 0x09 so it will start with a button press or after
# a timeout


# set root password
# apt-get update
# apt-get upgrade
# install python packages
# git clone https://github.com/abkfenris/gage-beaglebone.git
# add config
# setup powercape
# create gage service
# systemctl enable gage-logger.service
# add gagerun to /boot/uboot
# create Sample and Config tables


def apt_upgrade():
    """
    Update and upgrade apt
    """
    require.deb.uptodate_index(max_age={'day': 1})
    sudo('apt-get upgrade')


def gage_folder():
    """
    Folder for gage to run from
    """
    require.directory(gage_folder, use_sudo=True)


def git_gage():
    """
    Clone or update the gage-beaglebone repo
    """
    require.git.working_copy(
        'https://github.com/abkfenris/gage-beaglebone.git',
        path=gage_folder+'/gage-beaglebone',
        branch='master',
        update=True,
        use_sudo=True)


def install_requirements():
    """
    Install required packages
    """
    require.deb.package('python-smbus')
    require.deb.package('python-numpy')
    require.python.requirements(
        gage_folder+'/gage-beaglebone/gage-requirements.txt')


def git_powercape():
    """
    Clone or update the powercape git repo
    """
    require.git.working_copy(
        'https://github.com/AndiceLabs/PowerCape.git',
        path=gage_folder+'/powercape',
        branch='master',
        update=True,
        use_sudo=True
        )
    with cd(gage_folder+'/powercape/utils'):
        sudo('make powercape')


def powercape_update_bootloader():
    """
    Update the powercape bootloader

    http://andicelabs.com/2014/05/updating-power-cape-firmware/
    """
    with cd(gage_folder+'/powercape/utils'):
        sudo('./powercape -b')
    with cd(gage_folder+'/powercape/avr/twiboot/linux'):
        sudo('make')
        sudo('./twiboot -a 0x20 -w flask:powercape.hex')


def powercape_rtc_set():
    """
    Set the time on the powercape rtc
    """
    sudo('timedatectl')
    sudo('/usr/bin/ntpdate -b -s -u pool.ntp.org')
    sudo('timedatectl')
    with cd(gage_folder+'/powercape/utils'):
        sudo('./powercape -w')


def powercape_rtc_use():
    """
    Use powercape rtc for system time
    """
    pass


def powercape_startup_set():
    """
    Set powercape startup reasons
    """
    sudo('i2cset -y 1 0x21 7 {time}'.format(time=time_till_startup))
    sudo('i2cset -y 1 0x21 4 {reason}'.format(reason=startup_reasons))


def powercape_watchdog():
    pass


def clean_shutdown():
    """
    http://andicelabs.com/2014/07/automatic-root-filesystem-repair-boot/
    """


def bootstrap():
    """
    Setup all the things to make gage-beaglebone work
    """
    apt_upgrade()
    gage_folder()
    git_gage()
    git_powercape()
