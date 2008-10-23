#!/bin/sh

./del_rack.py --building np --rack 7 --aqservice $USER &
while [ "$?" = "0" ] ; do
	../../bin/aq status --aquser $USER
	../../bin/aq show hostiplist --aquser $USER
	sleep 5
	ps --ppid $$ --no-headers | grep -q del_rack
done

