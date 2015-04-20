#From https://sites.google.com/site/cellularbeaglebone/

echo Discovering USB port assignments
export tty_sierra=`/bin/dmesg | grep "USB modem converter now attached" | awk ' { tty1=tty2;tty2=tty3;tty3=tty4;tty4=$NF }  END { print tty1}'`
echo tty_sierra = $tty_sierra
echo $tty_sierra > /etc/tty_sierra
