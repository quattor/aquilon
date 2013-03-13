#!/usr/bin/env bash
#
# Copyright (C) 2012,2013  Contributor
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
