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
"""Remove dummy information for a rack of machines on a /26."""

from __future__ import print_function

import os
import sys

from common import AQRunner, TestNetwork, TestRack


def del_rack(building, rackid, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        for offset in range(1, 49):
            host = rack.get_host(half, offset)
            print("Checking that host exists before deleting.")
            rc = aq.wait(["show", "host", "--hostname", host])
            if rc == 0:
                print("Deleting host %s" % host)
                rc = aq.wait(["del", "host", "--hostname", host])
            machine = rack.get_machine(half, offset)
            print("Deleting machine %s" % machine)
            rc = aq.wait(["del", "machine", "--machine", machine])
        tor_switch = rack.get_tor_switch(half)
        "Deleting tor_switch %s" % tor_switch
        rc = aq.wait(["del", "tor_switch", "--tor_switch", tor_switch])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--building", dest="building", type="string",
                      help="The building name to use")
    parser.add_option("-r", "--rack", dest="rack", type="int",
                      help="The rack id to remove, 0-7")
    parser.add_option("-a", "--aqservice", dest="aqservice", type="string",
                      help="The service name to use when connecting to aqd")
    parser.add_option("-t", "--aqhost", dest="aqhost", type="string",
                      help="The aqd host to connect to")
    parser.add_option("-p", "--aqport", dest="aqport", type="string",
                      help="The port to use when connecting to aqd")
    (options, args) = parser.parse_args()
    if not options.building:
        parser.error("Missing option --building")
    if options.rack is None:
        parser.error("Missing option --rack")
    if options.rack not in range(8):
        parser.error("--rack must be 0-7")

    del_rack(options.building, options.rack,
             options.aqservice, options.aqhost, options.aqport)
