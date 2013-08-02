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
"""Run the different tests in serial to establish a baseline for timing."""


import os
from subprocess import Popen
from datetime import datetime
from optparse import OptionParser


DIR=os.path.realpath(os.path.dirname(__file__))

parser = OptionParser()
parser.add_option("-n", "--count", dest="count", type="int", default=4,
                  help="The number of repitions for the tests.")
parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                  help="The service name to use when connecting to aqd")
parser.add_option("-t", "--aqhost", dest="aqhost", type="string",
                  help="The aqd host to connect to")
parser.add_option("-p", "--aqport", dest="aqport", type="string",
                  help="The port to use when connecting to aqd")
(options, args) = parser.parse_args()

building = "np"

results = {}

results["add"] = []
for i in range(options.count):
    start = datetime.now()
    cmd = [os.path.join(DIR, "add_rack.py"), "--building", building,
           "--rack", str(i), "--subnet", str(i)]
    if options.aqservice:
        cmd.append("--aqservice")
        cmd.append(options.aqservice)
    if options.aqhost:
        cmd.append("--aqhost")
        cmd.append(options.aqhost)
    if options.aqport:
        cmd.append("--aqport")
        cmd.append(options.aqport)
    p = Popen(cmd, stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["add"].append(end-start)

results["update"] = []
for i in range(options.count):
    start = datetime.now()
    cmd = [os.path.join(DIR, "update_rack.py"), "--building", building,
           "--rack", str(i), "--subnet", str(i)]
    if options.aqservice:
        cmd.append("--aqservice")
        cmd.append(options.aqservice)
    if options.aqhost:
        cmd.append("--aqhost")
        cmd.append(options.aqhost)
    if options.aqport:
        cmd.append("--aqport")
        cmd.append(options.aqport)
    p = Popen(cmd, stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["update"].append(end-start)

results["show"] = []
for i in range(options.count):
    start = datetime.now()
    cmd = [os.path.join(DIR, "show_info.py")]
    if options.aqservice:
        cmd.append("--aqservice")
        cmd.append(options.aqservice)
    if options.aqhost:
        cmd.append("--aqhost")
        cmd.append(options.aqhost)
    if options.aqport:
        cmd.append("--aqport")
        cmd.append(options.aqport)
    p = Popen(cmd, stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["show"].append(end-start)

results["delete"] = []
for i in range(options.count):
    start = datetime.now()
    cmd = [os.path.join(DIR, "del_rack.py"), "--building", building,
           "--rack", str(i)]
    if options.aqservice:
        cmd.append("--aqservice")
        cmd.append(options.aqservice)
    if options.aqhost:
        cmd.append("--aqhost")
        cmd.append(options.aqhost)
    if options.aqport:
        cmd.append("--aqport")
        cmd.append(options.aqport)
    p = Popen(cmd, stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["delete"].append(end-start)

for key, values in results.items():
    if values:
        print
        print "%s:" % key
        print str(values)
        values.sort()
        min = values[0]
        print
        print "  min: %d.%d seconds" % (min.seconds, min.microseconds)
        max = values[-1]
        print "  max: %d.%d seconds" % (max.seconds, max.microseconds)
        print

#if __name__=='__main__':
