FROM resin/beaglebone-python:3.5

RUN apt-get update
RUN apt-get install -y \
    #python-smbus \
    #python3-numpy \
    minicom \
    gcc-avr \ 
    # may have an issue with gcc avr
    avr-libc \
    avrdude \
    unzip
# RUN pip install numpy use statistics in stdlib for stddev
# RUN sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"
# CMD apk add i2c-tools-dev --update-cache --allow-untrusted --repository http://dl-3.alpinelinux.org/alpine/edge/testing/

RUN mkdir gage
WORKDIR /gage

# RUN wget http://ftp.us.debian.org/debian/pool/main/i/i2c-tools/python3-smbus_3.1.2-3_armhf.deb
# RUN dpkg -i python3-smbus_3.1.2-3_armhf.deb
# RUN mv python3-smbus_3.1.2-3_armhf.deb /var/cache/apt/archives/
# RUN apt-get install -y python3-smbus

RUN git clone https://github.com/AndiceLabs/PowerCape.git
WORKDIR /gage/PowerCape/utils
RUN make

#CMD pip install spidev --no-cache-dir

WORKDIR /gage
COPY /app/gage-requirements.txt /gage
RUN pip install --no-cache-dir -r /gage/gage-requirements.txt

COPY app /gage

CMD while : ; do echo "Idling..."; sleep ${INTERVAL=600}; done
# CMD python simple.py