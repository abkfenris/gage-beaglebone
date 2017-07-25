FROM resin/beaglebone-black-python:3.6

RUN apt-get update
RUN apt-get install -y \
    minicom \
    gcc-avr \ 
    # may have an issue with gcc avr
    avr-libc \
    avrdude \
    unzip \
    libi2c-dev \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

# RUN sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"
RUN pip install --no-cache-dir --extra-index-url=https://gergely.imreh.net/wheels/ \
    cffi \
    smbus-cffi \
    dbus-python

RUN mkdir gage
WORKDIR /gage

RUN git clone https://github.com/AndiceLabs/PowerCape.git

# patch powercape to work on i2c bus 2
COPY /app/fix_powercape.patch /gage
WORKDIR /gage/PowerCape
RUN git apply /gage/fix_powercape.patch

# build powercape utils
WORKDIR /gage/PowerCape/utils
RUN make

# set label for SD card so that we can mount it
RUN echo "LABEL=GAGEDATA /mnt/gagedata vfat defaults" >> /etc/fstab

RUN mkdir /gage/app
WORKDIR /gage/app

COPY /app/requirements.txt /gage/app
RUN pip install --no-cache-dir --extra-index-url=https://gergely.imreh.net/wheels/ -r /gage/app/requirements.txt

COPY app /gage/app

#CMD while : ; do echo "Idling..."; sleep ${INTERVAL=600}; done

WORKDIR /gage
CMD python -m app.simple