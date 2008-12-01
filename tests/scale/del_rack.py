#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Remove dummy information for a rack of machines on a /26."""


import os
import sys

from common import AQRunner, TestNetwork, TestRack


def del_rack(building, rackid, aqservice):
    aq = AQRunner(aqservice=aqservice)
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    for half in [0, 1]:
        for offset in range(1, 49):
            host = rack.get_host(half, offset)
            print "Checking that host exists before deleting."
            rc = aq.wait(["show", "host", "--hostname", host])
            if rc == 0:
                print "Deleting host %s" % host
                rc = aq.wait(["del", "host", "--hostname", host])
            machine = rack.get_machine(half, offset)
            print "Deleting machine %s" % machine
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
    (options, args) = parser.parse_args()
    if not options.building:
        parser.error("Missing option --building")
    if options.rack is None:
        parser.error("Missing option --rack")
    if options.rack not in range(8):
        parser.error("--rack must be 0-7")

    del_rack(options.building, options.rack, options.aqservice)

