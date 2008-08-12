#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header: //eai/aquilon/aqd/1.2.1/src/etc/default-template.py#1 $
# $Change: 645284 $
# $DateTime: 2008/07/09 19:56:59 $
# $Author: wesleyhe $
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Remove dummy information for a rack of machines on a /26."""


from common import AQRunner, TestNetwork, TestRack


def del_rack(building, rackid):
    aq = AQRunner()
    rack = TestRack(building, rackid)
    rc = aq.wait(["ping"])
    half = 1
    offset = 35
    host = rack.get_host(half, offset)
    print "Deleting host %s" % host
    rc = aq.wait(["del", "host", "--hostname", host])
    machine = rack.get_machine(half, offset)
    print "Deleting machine %s" % machine
    rc = aq.wait(["del", "machine", "--machine", machine])


if __name__=='__main__':
    del_rack("np", 1)

