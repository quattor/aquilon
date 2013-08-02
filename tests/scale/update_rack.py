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
"""Update the dummy information for a rack of machines on a /26."""


import os
import sys

from common import AQRunner, TestNetwork, TestRack


def update_rack(building, rackid, newnetid, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        newnetwork = TestNetwork(newnetid, half)
        tor_switch = rack.get_tor_switch(half)
        print "Updating tor_switch %s" % tor_switch
        rc = aq.wait(["update", "interface", "--machine", tor_switch,
            "--interface", "xge49",
            "--mac", newnetwork.get_mac(0), "--ip", newnetwork.get_ip(0)])
        for offset in range(1, 49):
            machine = rack.get_machine(half, offset)
            print "Updating machine %s" % machine
            rc = aq.wait(["update", "interface", "--machine", machine,
                "--interface", "eth0", "--mac", newnetwork.get_mac(offset),
                "--ip", newnetwork.get_ip(offset)])
            host = rack.get_host(half, offset)
            print "reconfiguring host %s" % host
            rc = aq.wait(["reconfigure", "--hostname", host])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--building", dest="building", type="string",
                      help="The building name to use")
    parser.add_option("-r", "--rack", dest="rack", type="int",
                      help="The rack id to update, 0-7")
    parser.add_option("-s", "--subnet", dest="subnet", type="int",
                      help="The new subnet to use, 0-7")
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
    if options.subnet is None:
        parser.error("Missing option --subnet")
    if options.subnet not in range(8):
        parser.error("--subnet must be 0-7")

    update_rack(options.building, options.rack, options.subnet,
                options.aqservice, options.aqhost, options.aqport)
