#!/ms/dist/fsf/PROJ/bash/4.3/bin/bash -x
#
# Copyright (C) 2018  Contributor
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
set -o pipefail
TESTDIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
BASEDIR="$(dirname "$(dirname "$TESTDIR")")"

mkdir -p $BASEDIR/run

# Look for a couple of free ports to use
while true; do
    KNCPORT=$((RANDOM % 10000 + 10000))
    OPENPORT=$((KNCPORT + 1))
    GITPORT=$((KNCPORT + 2))
    if [ -z "$(/usr/sbin/ss -n -l -t sport = :$KNCPORT or sport = :$OPENPORT or sport = :$GITPORT | tail -n +2)" ]; then
	break
    fi
done

# Massage unittest.conf
sed     -e "s!^basedir =.*\$!basedir = $BASEDIR/run!" \
	-e "s/^kncport =.*$/kncport = ${KNCPORT}/" \
	-e "s/^openport =.*$/openport = ${OPENPORT}/" \
	-e "s/^git_port =.*$/git_port = ${GITPORT}/" \
	$TESTDIR/unittest.conf > \
	$BASEDIR/unittest.conf

# Make sure UNITTEST_FAILURE is returned if tests fail otherwise jenkins does not mark build as failed
$TESTDIR/runtests.py --config $BASEDIR/unittest.conf --coverage 2>&1 --no-interactive | tee $TESTDIR/aqdtests.log
if [ $(grep -c '^OK$' $TESTDIR/aqdtests.log 2>/dev/null) -ne 2 ]; then
    echo UNITTEST_FAILURE
    exit 1
fi
