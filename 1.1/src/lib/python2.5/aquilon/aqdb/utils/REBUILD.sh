#!/bin/bash

DBFILE=/var/tmp/`whoami`/aquilondb/aquilon.db
if [ -r "$DBFILE" ] ; then
	mv "$DBFILE" "$DBFILE.saved"
	echo "moved existing db to '$DBFILE.saved'"
fi

time ./location.py
echo
time ./network.py
echo
time ./service.py
echo
time ./configuration.py
echo
time ./hardware.py
echo
time ./interfaces.py
echo 
time ./build.py
echo
time ./auth.py
echo
