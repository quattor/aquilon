#!/ms/dist/fsf/PROJ/bash/4.3/bin/bash
#
# Copyright (C) 2008,2009,2010,2011,2013,2016,2018  Contributor
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
DIR="$(cd $(dirname "${BASH_SOURCE[0]}") && pwd)"
restart_from=$(grep -oP "(?<='train test -t restart' command. Last test failed: ).*$" $DIR/aqdtests.log)
if [ -z "$restart_from" ]; then
    echo "Re-starting point not found" >&2
    return -1
fi
echo "Re-starting tests from: $restart_from" >&2
$DIR/runtests.py --config=$DIR/unittest.conf --failfast --no-interactive --start $restart_from | tee $DIR/aqdtests.log
