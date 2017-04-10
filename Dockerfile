FROM resin/beaglebone-python:3.6

RUN apt-get update
RUN apt-get install -y \
    #python-smbus \
    python3-numpy \
    minicom \
    gcc-avr \ 
    # may have an issue with gcc avr
    avr-libc \
    avrdude \
    unzip
# RUN sh -c "echo 'BB-UART2' > /sys/devices/platform/bone_capemgr/slots"
# CMD apk add i2c-tools-dev --update-cache --allow-untrusted --repository http://dl-3.alpinelinux.org/alpine/edge/testing/

RUN mkdir gage
WORKDIR /gage
RUN git clone https://github.com/AndiceLabs/PowerCape.git
WORKDIR /gage/PowerCape/utils
CMD make powercape && make

#CMD pip install spidev --no-cache-dir

COPY /app/gage-requirements.txt /gage
RUN pip install --no-cache-dir -r /gage/gage-requirements.txt

COPY app /gage

CMD while : ; do echo "Idling..."; sleep ${INTERVAL=600}; done
# CMD python simple.py