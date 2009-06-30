#!/usr/bin/env bash

if [[ "$BASH_SOURCE" == "$0" ]] ; then
	echo
	echo "WARNING: This script is meant to be sourced instead of"
	echo "         being called directly!"
	echo
	echo "Try running as:"
	echo ". $0"
	echo "or"
	echo "AQDCONF=/path/to/new/conf . $0"
	echo
fi

SRCDIR=$(python2.5 -c 'import os, sys; print os.path.realpath(os.path.join(os.path.dirname(sys.argv[1]), ".."))' "$0")

if [ -z "$AQDCONF" ] ; then
	AQDCONF="$SRCDIR/etc/aqd.conf.dev"
else
	AQDCONF=$(python2.5 -c 'import os, sys; print os.path.realpath(sys.argv[1])' "$AQDCONF")
fi

AQUSER=$("$SRCDIR/lib/python2.5/aquilon/config.py" | grep -A 1000 "\[broker\]" | grep "user=" | head -1 | cut -d= -f2)
AQHOST=$("$SRCDIR/lib/python2.5/aquilon/config.py" | grep -A 1000 "\[broker\]" | grep "hostname=" | head -1 | cut -d= -f2)
AQPORT=$("$SRCDIR/lib/python2.5/aquilon/config.py" | grep -A 1000 "\[broker\]" | grep "kncport=" | head -1 | cut -d= -f2)

echo
echo "Using srcdir  = $SRCDIR"
echo "  and AQDCONF = $AQDCONF"
echo "where AQUSER  = $AQUSER"
echo "  and AQPORT  = $AQPORT"
echo "  and AQHOST  = $AQHOST"
echo

function devaq() { $SRCDIR/bin/aq.py "$@" --aqhost $AQHOST --aquser $AQUSER --aqport $AQPORT ; }

type devaq

# Note: Due to shell semantics if this script was called as:
# $ AQDCONF=/path/to/new/aqd.conf . $0
# Then the shell will set AQDCONF back to whatever it was before sourcing
# this script and this export is meaningless.
export AQDCONF AQUSER AQHOST AQPORT devaq

