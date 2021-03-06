"""
Fabric commands to setup beaglebone
"""
from fabric.api import cd, env, lcd, put, prompt, local, sudo, prefix
from fabric.decorators import runs_once
from fabric.contrib.files import exists, sed
from fabric.contrib.console import confirm
from fabtools import require
import fabtools
import inspect
import importlib

from cell import sprint

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


def mk_gage_folder():
    """
    Folder for gage to run from
    """
    require.directory(gage_folder, use_sudo=True)


def git_gage():
    """
    Clone or update the gage-beaglebone repo

    If it fails check that the time is correct
    """
    #sudo('systemctl stop gage-logger.service')
    require.git.working_copy(
        'https://github.com/abkfenris/gage-beaglebone.git',
        path=gage_folder+'/gage-beaglebone',
        branch='feature/sprint',
        update=True,
        use_sudo=True)
    with cd(gage_folder+'/gage-beaglebone'):
        # initialize and update the submodule
        sudo('git submodule init')
        sudo('git submodule update')


def python_requirements():
    """
    Install required packages for python
    """
    require.deb.packages(['python-smbus', 'python-numpy', 'minicom'])
    require.python.requirements(
        gage_folder+'/gage-beaglebone/gage-requirements.txt')


def powercape_requirements():
    """
    Install requirements for powercape
    """
    require.deb.packages(['gcc-avr', 'avr-libc', 'avrdude', 'unzip'])


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
        sudo('make')


def powercape_update_bootloader():
    """
    Update the powercape bootloader

    http://andicelabs.com/2014/05/updating-power-cape-firmware/
    """
    with cd('/gage'):
        sudo('wget http://andicelabs.com/wp-content/uploads/2014/08/powercape.zip')
        sudo('unzip powercape.zip')
    with cd(gage_folder+'/powercape/utils'):
        sudo('./power -b')
    with cd(gage_folder+'/powercape/avr/twiboot/linux'):
        # sudo('make')
        sudo('./twiboot -a 0x20 -w flash:/gage/powercape.hex')
    with cd('/gage'):
        sudo('rm powercape.hex')
        sudo('rm powercape.zip')


def powercape_rtc_set():
    """
    Set the time on the powercape rtc
    """
    sudo('date')
    sudo('ntpdate -b -s -u pool.ntp.org')
    sudo('date')
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
    sed('/lib/init/vars.sh', 'FSCKFIX=no', 'FSCKFIX=yes', use_sudo=True)


def shutdown():
    """
    Shut the beaglebone down
    """
    sudo('shutdown -h now')


@runs_once
def _settings():
    """
    Get settings
    """
    settings = {}
    settings['name'] = prompt('Gage name?')
    settings['id_num'] = prompt('Gage id number?')
    settings['secret_key'] = prompt('Secret gage password?')
    settings['depth_ain'] = prompt('Depth AIN?')
    settings['depth_gpio'] = prompt('Depth GPIO?')
    settings['depth_uart'] = prompt('Depth UART?')
    settings['serial_dev'] = prompt('Serial Device?')
    settings['url'] = prompt('API post URL?')
    settings['restart_time'] = prompt('Time between shutdown and start?')
    # get cell connection options
    options = []
    for cls in inspect.getmembers(sprint, inspect.isclass):
        if not cls[0] == 'CellConnection':
            options.append(cls)
    print 'Cellular options:'
    for i, cls in enumerate(options):
        print('  {num} - {cls}'.format(num=i, cls=cls))
    choice = options[int(prompt('Enter number for cell connection type'))][1]
    settings['cell_base'] = choice.__module__
    settings['cell_import'] = choice.__name__
    settings['startup_reasons'] = startup_reasons
    return settings


def make_config():
    """
    Make config file and place on gage
    """
    settings = _settings()
    fabtools.files.upload_template(
        'templates/config-template.py',
        '/gage/gage-beaglebone/config.py',
        context=settings,
        use_sudo=True,
        use_jinja=True
    )


def service_add():
    """
    Add the systemd service
    """
    with cd('/lib/systemd/system'):
        require.file('gage-logger.service',
                     source='gage-logger.service',
                     use_sudo=True)
        sudo('systemctl enable gage-logger.service')


def service_start():
    """
    Start the service
    """
    sudo('systemctl start gage-logger.service')


def gagerun():
    """
    Add gagerun to uboot so that it will go do it's thing
    """
    sudo('touch /boot/uboot/gagerun')


def gagestop():
    """
    Add gagestop to uboot so that the logging cycle will stop
    """
    sudo('touch /boot/uboot/gagestop')


def setup_cell():
    """
    Setup cell by getting settings option, and install files
    """
    settings = _settings()
    cell_base = settings['cell_base']
    cell_import = settings['cell_import']
    Cellmod = importlib.import_module(cell_base)
    Cell = getattr(Cellmod, cell_import)
    c = Cell()
    c.install()


def bootstrap():
    """
    Setup all the things to make gage-beaglebone work
    """
    #apt_upgrade()
    #clean_shutdown()
    #mk_gage_folder()
    #git_gage()
    python_requirements()
    #git_powercape()
    #powercape_requirements()
    #powercape_startup_set()
    #service_add()
    #gagerun()
