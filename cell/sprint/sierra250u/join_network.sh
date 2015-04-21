#From https://sites.google.com/site/cellularbeaglebone/

export SHELL=/bin/sh
export TERM=vt100
export USER=root
export PATH=/usr/local/bin:/usr/bin:/bin:/usr/local/sbin:/usr/sbin:/sbin
export PWD=/home/root
export HOME=/home/root
export SHLVL=2
exportLOGNAME=root

#The script included jusb below gets the right USB port in an /etc/tty_sierra file
/home/root/usb_discover.sh

#The my_provider is a template of options lacking the usb port
cat /home/root/my_provider > /etc/ppp/peers/provider

export ttystring=/dev/`cat /etc/tty_sierra`
echo $ttystring >> /etc/ppp/peers/provider

echo First shut off ppp if it is running
/usr/bin/poff
sleep 5

echo Now turning on ppp
/usr/bin/pon &
sleep 30

echo Now updating the resolver with saved resolver nameservers
cp /etc/open.resolv.conf /etc/resolv.conf
cat /etc/resolv.conf
export gw=`ifconfig ppp0 |grep inet | awk '{print $3}'|sed /P-t-P:/s///`
export PPP0=`ifconfig ppp0 | grep "inet addr" | awk '{ print $2 }' | awk 'BEGIN { FS=":" } { print $2 }'`
echo PPP0=$PPP0
if [ -z ${PPP0} ]
then
        echo Network Failed
else
        echo Network Joined
        echo Adding a default route
        /sbin/route add -net 0.0.0.0 gw $PPP0
        echo Network Ready
fi