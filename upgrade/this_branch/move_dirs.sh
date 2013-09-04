#! /bin/sh

AQD_CONFIG="../../bin/aqd_config"
if [ ! -x "$AQD_CONFIG" ]; then
	AQD_CONFIG="$AQD_CONFIG.py"
fi

quattordir=`$AQD_CONFIG --get broker.quattordir`
if [ -z "$quattordir" ]; then
	echo "Failed to determine broker.quattordir" 1>&2
	exit 1
fi

if [ -z "$1" ]; then
	old_build="$quattordir/build/xml"
	new_build="$quattordir/build"
	revert=0
elif [ "$1" == "--revert" ]; then
	old_build="$quattordir/build"
	new_build="$quattordir/build/xml"
	revert=1
else
	echo "Usage: $0 [--revert]" 1>&2
	exit 1
fi

if [ ! -d "$old_build" ]; then
	echo "$old_build does not exist" 1>&2
	exit 1
fi

echo "Will move the contents of $old_build to $new_build"
echo ""
echo "Press ENTER to proceed, Ctrl+C to abort."

read dummy

if [ $revert == 1 ]; then
	set -x
	mkdir -p "$new_build"
	set +x
fi

set -x
find "$old_build" -mindepth 1 -maxdepth 1 -type d -not -name "xml" -execdir mv --verbose '{}' "$new_build/" ';'
set +x

if [ $revert == 0 ]; then
	set -x
	rmdir "$old_build"
	set +x

	echo ""
	echo "If you want to revert the changes, run:"
	echo "$0 --revert"
fi
