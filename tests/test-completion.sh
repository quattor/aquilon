#!/usr/bin/env bash
completion_file=$1
if [[ ! -f $completion_file ]]; then
    echo "usage: $0 <filename>"
    exit 1
fi
. $completion_file

total_fail=0
for obj in $( perl -ne '/_aq_complete_(.*) \(\)/ && print "$1\n"' $completion_file) ; do 
    echo -n "test $obj..."
    output=$(_aq_complete_$obj 2>&1)
    if [[ $? == 0 ]]; then
        echo "ok"
    else
        echo "failed: $output"
        total_fail=$(( total_fail + 1 ))
    fi
done
exit $total_fail
