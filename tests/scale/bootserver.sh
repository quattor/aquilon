#!/bin/sh
#
# Copyright (C) 2011,2013  Contributor
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

# Standalone script meant to run against a dev copy of production.
# This mimics some of the behavior of multiple bootservers asking for
# information while a rack is being reconfigured.

AQHOST=$(hostname)
#AQUSER=$USER
AQUSER=aqdqa
export AQHOST AQUSER
# Set --aqport if needed
AQKNC="--aqport=6902"
AQOPEN="--noauth --aqport=6901"

cd $(dirname $0)
AQ=../../bin/aq.py

hosts=$($AQ search host --domain ny-prod --personality infra $AQOPEN | head -20)
instances=$($AQ show service --service bootserver $AQOPEN | grep Instance | awk '{print $4}' | head -10)

$AQ show network --building dd --format proto $AQKNC >/dev/null &
$AQ show network --building ds --format proto $AQKNC >/dev/null &
for h in $hosts
do
	$AQ reconfigure --hostname $h $AQKNC >/dev/null &
done
for i in $instances
do
	$AQ show map --service bootserver --instance $i --format=proto $AQOPEN >/dev/null &
done

time wait
