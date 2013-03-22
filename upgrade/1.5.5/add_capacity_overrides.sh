#! /bin/sh
#
# Copyright (C) 2010,2013  Contributor
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

# This scripts determines which clusters are above capacity, and prints out the
# appropriate capacity override aq commands. The commands then have to be
# executed manually.

WORKDIR=`mktemp -t -d aqupgrade-XXXXXX`

trap "rm -rf $WORKDIR" EXIT SIGINT

# Get the list of ESX clusters
echo "# Getting the list of clusters..."
aq search esx cluster --all > "$WORKDIR"/cluster_list
for cluster in `cat $WORKDIR/cluster_list`; do
	echo "# Getting info for $cluster..."
	aq show esx cluster --cluster $cluster > "$WORKDIR/$cluster"
done

echo "# Capacity override commands to execute:"

# Do the checks
for cluster in `cat $WORKDIR/cluster_list`; do
	# The only resource we support right now is memory
	capacity=`awk '/Capacity limits: memory:/ { print $4 }' "$WORKDIR/$cluster"`
	usage=`awk '/Resources used by VMs: memory:/ { print $6 }' "$WORKDIR/$cluster"`

	# If there is no limit or there is no usage, skip
	if [ -z "$capacity" -o -z "$usage" ]; then
		continue
	fi

	# Skip if not over capacity
	if [ $capacity -ge $usage ]; then
		continue
	fi

	echo "aq update esx cluster --cluster $cluster --memory_capacity $usage"
done
