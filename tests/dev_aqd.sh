#!/bin/sh

STARTDIR=`dirname $0`

if [ -z "$AQDCONF" ] ; then
	AQDCONF="$STARTDIR/../etc/aqd.conf.dev"
	export AQDCONF
fi

BASEDIR=`$STARTDIR/../lib/python2.6/aquilon/config.py | grep -A 1000 "\[broker\]" | grep "basedir=" | head -1 | cut -c9-`

if [ -z "$BASEDIR" ]; then
	echo "Failed to determine the base directory" >&2
	exit 1
fi

RUNDIR=`$STARTDIR/../lib/python2.6/aquilon/config.py | grep -A 1000 "\[broker\]" | grep "rundir=" | head -1 | cut -c8-`
DSN=`$STARTDIR/../lib/python2.6/aquilon/config.py | grep -A 1000 "\[database\]" | grep "dsn=" | head -1 | cut -c5-`

echo
echo "Using AQDCONF = $AQDCONF"
echo "where basedir = $BASEDIR"
echo "  and rundir  = $RUNDIR"
echo "  and dsn     = $DSN"
echo

exec python2.6 "$STARTDIR/../bin/twistd.py" -no -l - --pidfile=$RUNDIR/aqd.pid aqd --config=$AQDCONF "$@"

