#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Add dummy information for a rack of machines on a /26."""


import os
import sys

from common import AQRunner, TestNetwork, TestRack


def add_rack(building, rackid, netid, aqservice, aqhost, aqport):
    aq = AQRunner(aqservice=aqservice, aqhost=aqhost, aqport=aqport)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        network = TestNetwork(netid, half)
        tor_switch = rack.get_tor_switch(half)
        "Adding a tor_switch"
        rc = aq.wait(["add", "tor_switch", "--tor_switch", tor_switch,
            "--building", building, "--rackid", rack.rackid,
            "--model", "rs g8000", "--interface", "xge49",
            "--rackrow", rack.row, "--rackcolumn", rack.column,
            "--mac", network.get_mac(0), "--ip", network.get_ip(0)])
        domain = "testdom_odd" if rackid % 2 else "testdom_even"
        for offset in range(1, 49):
            machine = rack.get_machine(half, offset)
            print "Adding machine %s" % machine
            rc = aq.wait(["add", "machine", "--machine", machine,
                "--model", "vb1205xm", "--rack", rack.get_rack()])
            print "Adding an interface with %s" % network.get_mac(offset)
            rc = aq.wait(["add", "interface", "--machine", machine,
                          "--interface", "eth0",
                          "--mac", network.get_mac(offset)])
            host = rack.get_host(half, offset)
            print "Adding host %s with %s" % (host, network.get_ip(offset))
            rc = aq.wait(["add", "host", "--machine", machine,
                          "--hostname", host, "--archetype", "aquilon",
                          "--domain", domain, "--buildstatus", "blind",
                          "--ip", network.get_ip(offset)])
            print "make aquilon for host %s" % host
            rc = aq.wait(["make", "aquilon", "--hostname", host,
                          "--os", "linux/5.0.1-x86_64",
                          "--personality", "compileserver"])


if __name__=='__main__':
    from optparse import OptionParser

    parser = OptionParser()
    parser.add_option("-b", "--building", dest="building", type="string",
                      help="The building name to use")
    parser.add_option("-r", "--rack", dest="rack", type="int",
                      help="The rack id to use, 0-7")
    parser.add_option("-s", "--subnet", dest="subnet", type="int",
                      help="The subnet to use, 0-7")
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

    add_rack(options.building, options.rack, options.subnet,
             options.aqservice, options.aqhost, options.aqport)
