#!/bin/bash
#
# Copyright (C) 2008,2013  Contributor
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

# chkconfig: 35 99 01
# description: runs an aqd broker

# Source function library.
. /etc/init.d/functions

RETVAL=0
prog="aqd"
pidfile="/var/quattor/run/aqd.pid"
aqd="/ms/dist/aquilon/PROJ/aqd/prod/bin/aqd"
conffile="/etc/aqd.conf"
orcl_client="orcl/10.2.0.1.0"
MODULEPATH="/ms/dist/aurora/etc/modules"

start() {
        echo -n $"Starting $prog: "
	export MODULEPATH
	eval `/ms/dist/aurora/bin/modulecmd bash load $orcl_client`
	su cdb -c "/ms/dist/aurora/bin/krun -afs -- $aqd --pidfile=$pidfile --logfile=/var/quattor/logs/aqd.log aqd --config=$conffile " >/var/quattor/logs/aqd.out 2>&1
	RETVAL=$?
	if [ $RETVAL -eq 0 ]; then
            touch /var/lock/subsys/$prog
	    success $"$prog startup"
	else
	    failure $"$prog startup"
	fi
        echo
	return $RETVAL
}

stop() {
        echo -n $"Shutting down $prog: "
	RETVAL=0
	if [ -f $pidfile ]; then
		pid=
		read line < $pidfile
		for p in $line ; do
			if [ -z "${p//[0-9]/}" -a -d "/proc/$p" ]; then
				pid="$p"
			fi
		done
		if [ -n "${pid:-}" ]; then
			if checkpid $pid 2>&1; then
				kill -TERM $pid > /dev/null 2>&1
				usleep 100000
				if checkpid $pid && sleep 1 && 
				   checkpid $pid && sleep 3 &&
				   checkpid $pid ; then
					kill -KILL $pid >/dev/null 2>&1
					usleep 100000
				fi
			fi
			checkpid $pid
			RETVAL=$?
		fi
		rm -f $pidfile
	fi

	[ "$RETVAL" -eq 0 ] && success $"$prog shutdown" || success $"$prog shutdown"
        echo
	rm -f /var/lock/subsys/$prog
	return $RETVAL
}

aqstatus() {
	if [ -f $pidfile ]; then
		read pid < $pidfile
		if [ -n "$pid" ]; then
			if checkpid $pid 2>&1; then
				echo $"${prog} is running"
				return 0
			else
				echo $"${prog} is dead but pid file exists"
				return 1
			fi
		fi
	fi
	if [ -f /var/lock/subsys/$prog ]; then
		echo $"${prog} is dead but subsys locked"
		return 1
	fi
	echo $"${prog} is stopped"
	return 0
}

# See how we were called.
case "$1" in
  start)
	start
        ;;
  stop)
	stop
        ;;
  status)
	aqstatus
	RETVAL=$?
	;;
  restart|reload)
	stop
	start
	RETVAL=$?
	;;
  condrestart)
	if [ -f /var/lock/subsys/$prog ]; then
	    stop
	    start
	    RETVAL=$?
	fi
	;;
  *)
        echo $"Usage: $0 {start|stop|restart|condrestart|status}"
        exit 1
esac

exit $RETVAL
