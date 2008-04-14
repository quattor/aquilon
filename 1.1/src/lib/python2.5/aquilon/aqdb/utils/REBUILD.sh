#!/bin/bash

DBFILE=/var/tmp/`whoami`/aquilondb/aquilon.db
if [ -r "$DBFILE" ] ; then
	mv "$DBFILE" "$DBFILE.saved"
	echo "moved existing db to '$DBFILE.saved'"
fi

IPY='/ms/dist/python/PROJ/ipython/0.7.2/bin/ipython '

echo starting at 
/bin/date

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
time ./interface.py
echo 
time ./service.py
echo
time ./population_scripts.py
echo completed at
/bin/date
