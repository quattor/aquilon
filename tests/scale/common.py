#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Some common utilities used by the scale tests."""


import os
from subprocess import Popen


class TestRack(object):
    def __init__(self, building, rackid):
        self.building = building
        self.rackid = rackid
        self.row = building[0]
        self.column = rackid

    def get_rack(self):
        return "%s%s" % (self.building, self.rackid)

    def get_tor_switch(self, half):
        return "%s%sgd1r%02d.one-nyp.ms.com" % (self.building,
                                                self.rackid, half)

    def get_machine(self, half, offset):
        return "%s%ss1%02dp%d" % (self.building, self.rackid, half, offset)

    def get_host(self, half, offset):
        return "scaletest%d.one-nyp.ms.com" % (100*self.rackid+48*half+offset)


class TestNetwork(object):
    networks = [[8, 8, 4, [  1,  65]],
                [8, 8, 4, [129, 193]],
                [8, 8, 5, [  1,  65]],
                [8, 8, 5, [129, 193]],
                [8, 8, 6, [  1,  65]],
                [8, 8, 6, [129, 193]],
                [8, 8, 7, [  1,  65]],
                [8, 8, 7, [129, 193]]]

    def __init__(self, network, half):
        self.first = self.networks[network][0]
        self.second = self.networks[network][1]
        self.third = self.networks[network][2]
        self.fourth = self.networks[network][3][half]

    def get_mac(self, offset):
        return "02:02:%02x:%02x:%02x:%02x" % (
                self.first, self.second, self.third, self.fourth + offset + 8)

    def get_ip(self, offset):
        return "%d.%d.%d.%d" % (
                self.first, self.second, self.third, self.fourth + offset + 8)


class AQRunner(object):
    def __init__(self, aq=None, host=None, port=None, aqservice=None):
        self.aq = aq or os.path.realpath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'bin', 'aq'))
        #self.aq = aq or "/ms/dist/aquilon/PROJ/aqd/prod/bin/aq"
        #self.host = host or "oyidb1622"
        self.host = host or None
        self.port = port or None
        self.aqservice = aqservice or None

    def run(self, args, **kwargs):
        full_args = [str(self.aq)]
        full_args.extend([str(arg) for arg in args])
        if self.host:
            full_args.append("--aqhost")
            full_args.append(str(self.host))
        if self.port:
            full_args.append("--aqport")
            full_args.append(str(self.port))
        if self.aqservice:
            full_args.append("--aquser")
            full_args.append(str(self.aqservice))
        if not kwargs.has_key("stdout"):
            kwargs["stdout"] = 1
        if not kwargs.has_key("stderr"):
            kwargs["stderr"] = 2
        return Popen(full_args, **kwargs)

    def wait(self, args, **kwargs):
        p = self.run(args, **kwargs)
        p.wait()
        return p.returncode


#if __name__=='__main__':
