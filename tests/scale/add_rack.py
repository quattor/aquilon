#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Add dummy information for a rack of machines on a /26."""


import os
import sys

if __name__=='__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..',
                                                     "lib", "python2.5")))

from common import AQRunner, TestNetwork, TestRack


def add_rack(building, rackid, netid, aqservice):
    aq = AQRunner(aqservice=aqservice)
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
                          "--domain", "testdom", "--buildstatus", "blind",
                          "--ip", network.get_ip(offset)])
            print "make aquilon for host %s" % host
            rc = aq.wait(["make", "aquilon", "--hostname", host,
                          "--os", "linux/4.0.1-x86_64",
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

    add_rack(options.building, options.rack, options.subnet, options.aqservice)

