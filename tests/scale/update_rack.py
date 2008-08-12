#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/etc/default-template.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Update the dummy information for a rack of machines on a /26."""


from common import AQRunner, TestNetwork, TestRack


def update_rack(building, rackid, newnetid):
    aq = AQRunner()
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

    update_rack(options.building, options.rack, options.subnet)

