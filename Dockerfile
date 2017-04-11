FROM resin/beaglebone-python:3.6

RUN apt-get update
RUN apt-get install -y \
    minicom \
    gcc-avr \ 
    # may have an issue with gcc avr
    avr-libc \
    avrdude \
    unzip \
    libi2c-dev

# RUN sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"
RUN pip install --no-cache-dir cffi
RUN pip install --no-cache-dir smbus-cffi

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

WORKDIR /gage
COPY /app/gage-requirements.txt /gage
RUN pip install --no-cache-dir -r /gage/gage-requirements.txt

COPY app /gage

# CMD while : ; do echo "Idling..."; sleep ${INTERVAL=600}; done
CMD python simple.py