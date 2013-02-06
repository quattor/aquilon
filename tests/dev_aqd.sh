#!/bin/sh

STARTDIR=`dirname $0`

if [ -z "$AQDCONF" ] ; then
	AQDCONF="$STARTDIR/../etc/aqd.conf.dev"
	export AQDCONF
fi

BASEDIR=`$STARTDIR/../bin/aqd_config.py --get broker.basedir`

if [ -z "$BASEDIR" ]; then
	echo "Failed to determine the base directory" >&2
	exit 1
fi

RUNDIR=`$STARTDIR/../bin/aqd_config.py --get broker.rundir`
DSN=`$STARTDIR/../bin/aqd_config.py --get database.dsn`

echo
echo "Using AQDCONF = $AQDCONF"
echo "where basedir = $BASEDIR"
echo "  and rundir  = $RUNDIR"
echo "  and dsn     = $DSN"
echo

exec python2.6 "$STARTDIR/../bin/twistd.py" -no -l - --pidfile=$RUNDIR/aqd.pid aqd --config=$AQDCONF "$@"

