#!/bin/bash

mv /var/tmp/`whoami`/aquilondb/aquilon.db  /var/tmp/`whoami`/aquilondb/saved.db

time ./location.py

time ./network.py

time ./service.py

time ./configuration.py

time ./hardware.py

time ./interfaces.py

