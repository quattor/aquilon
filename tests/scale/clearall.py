#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Clean up any entries."""


import os
from subprocess import Popen


DIR=os.path.realpath(os.path.dirname(__file__))
free_racks = range(8)
free_subnets = range(8)
building = "np"

processes = []
for rackid in free_racks:
    processes.append(Popen([os.path.join(DIR, "del_rack.py"),
        "--building", building, "--rack", str(rackid)], stdout=1, stderr=2))

for process in processes:
    process.wait()


#if __name__=='__main__':
