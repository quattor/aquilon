#!/bin/sh
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

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

exec python2.6 "$STARTDIR/../sbin/aqd.py" -no -l - --pidfile=$RUNDIR/aqd.pid aqd --config=$AQDCONF "$@"

