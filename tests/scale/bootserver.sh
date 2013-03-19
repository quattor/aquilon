#!/bin/sh

# Standalone script meant to run against a dev copy of production.
# This mimics some of the behavior of multiple bootservers asking for
# information while a rack is being reconfigured.

AQHOST=$(hostname)
#AQUSER=$USER
AQUSER=aqdqa
export AQHOST AQUSER
# Set --aqport if needed
AQKNC="--aqport=6902"
AQOPEN="--noauth --aqport=6901"

cd $(dirname $0)
AQ=../../bin/aq.py

hosts=$($AQ search host --domain ny-prod --personality infra $AQOPEN | head -20)
instances=$($AQ show service --service bootserver $AQOPEN | grep Instance | awk '{print $4}' | head -10)

$AQ show network --building dd --format proto $AQKNC >/dev/null &
$AQ show network --building ds --format proto $AQKNC >/dev/null &
for h in $hosts
do
	$AQ reconfigure --hostname $h $AQKNC >/dev/null &
done
for i in $instances
do
	$AQ show map --service bootserver --instance $i --format=proto $AQOPEN >/dev/null &
done

time wait
