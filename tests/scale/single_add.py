#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/etc/default-template.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Add dummy information for a rack of machines on a /26."""


from common import AQRunner, TestNetwork, TestRack


def add_rack(building, rackid, netid):
    aq = AQRunner()
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    half = 1
    network = TestNetwork(netid, half)
    offset = 35
    machine = rack.get_machine(half, offset)
    print "Adding machine %s" % machine
    rc = aq.wait(["add", "machine", "--machine", machine,
        "--model", "vb1205xm", "--rack", rack.get_rack()])
    print "Adding an interface with %s" % network.get_mac(offset)
    rc = aq.wait(["add", "interface", "--machine", machine,
        "--interface", "eth0", "--mac", network.get_mac(offset),
        "--ip", network.get_ip(offset)])
    host = rack.get_host(half, offset)
    print "Adding host %s with %s" % (host, network.get_ip(offset))
    rc = aq.wait(["add", "host", "--machine", machine,
        "--hostname", host, "--archetype", "aquilon",
        "--domain", "testdom", "--status", "production"])
    print "make aquilon for host %s" % host
    rc = aq.wait(["make", "aquilon", "--hostname", host,
        "--os", "linux/4.0.1-x86_64",
        "--personality", "ms/fid/spg/ice"])


if __name__=='__main__':
    add_rack("np", 1, 0)

