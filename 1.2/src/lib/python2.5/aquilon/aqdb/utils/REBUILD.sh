#!/bin/bash -e

if [ -z "$AQDBFILE" ] ; then
	AQDBFILE=/var/tmp/`whoami`/aquilondb/aquilon.db
fi
if [ -r "$AQDBFILE" ] ; then
	mv "$AQDBFILE" "$AQDBFILE.saved"
	echo "moved existing db to '$AQDBFILE.saved'"
fi

IPY='/ms/dist/python/PROJ/ipython/0.7.2/bin/ipython '

echo starting at
/bin/date

time ./locationType.py
echo
time ./location.py
echo
time ./network.py
echo
time ./auth.py
echo
time ./configuration.py
echo
time ./hardware.py
echo
time ./interfaceType.py
echo
time ./interface.py
echo
time ./systemType.py
echo
time ./systems.py
echo
time ./service.py
echo
time ./switch_port.py
echo Run population_scripts if you need to
#time ./population_scripts.py
echo completed at
/bin/date
