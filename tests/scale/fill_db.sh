#!/bin/sh -ex
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

./setup.py
for i in 0 1 2 3 4 5 6 7; do
	./add_rack.py --building np --rack $i --subnet $i --aqservice $USER &
done

wait
echo "Take a snapshot of the db..."

