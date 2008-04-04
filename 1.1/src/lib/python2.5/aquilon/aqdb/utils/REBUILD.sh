#!/bin/bash

mv /var/tmp/`whoami`/aquilondb/aquilon.db  /var/tmp/`whoami`/aquilondb/saved.db
echo 'move existing db to 'saved.db'

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
time ./auth.py
echo
