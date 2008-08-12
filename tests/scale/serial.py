#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/etc/default-template.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Run the different tests in serial to establish a baseline for timing."""


import os
from subprocess import Popen
from datetime import datetime


DIR=os.path.realpath(os.path.dirname(__file__))
building = "np"

results = {}

results["add"] = []
for i in range(4):
    start = datetime.now()
    p = Popen([os.path.join(DIR, "add_rack.py"), "--building", building,
        "--rack", str(i), "--subnet", str(i)], stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["add"].append(end-start)

results["update"] = []
for i in range(4):
    start = datetime.now()
    p = Popen([os.path.join(DIR, "update_rack.py"), "--building", building,
        "--rack", str(i), "--subnet", str(i+4)], stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["update"].append(end-start)

results["show"] = []
for i in range(4):
    start = datetime.now()
    p = Popen([os.path.join(DIR, "show_info.py")], stdout=1, stderr=2)
    p.wait()
    end = datetime.now()
    results["show"].append(end-start)

results["delete"] = []
for i in range(4):
    start = datetime.now()
    p = Popen([os.path.join(DIR, "del_rack.py"), "--building", building,
        "--rack", str(i)], stdout=1, stderr=2)
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
