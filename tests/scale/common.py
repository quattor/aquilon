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
"""Some common utilities used by the scale tests."""


import os
import socket
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
    def __init__(self, aq=None, aqhost=None, aqport=None, aqservice=None):
        self.aq = aq or os.path.realpath(os.path.join(
            os.path.dirname(__file__), '..', '..', 'bin', 'aq.py'))
        # The default for dist or dev is to use prod, and we really don't
        # want to use prod by default for these tests...
        self.host = aqhost or socket.gethostname()
        self.port = aqport or None
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
            full_args.append("--aqservice")
            full_args.append(str(self.aqservice))
        if "stdout" not in kwargs:
            kwargs["stdout"] = 1
        if "stderr" not in kwargs:
            kwargs["stderr"] = 2
        return Popen(full_args, **kwargs)

    def wait(self, args, **kwargs):
        p = self.run(args, **kwargs)
        p.wait()
        return p.returncode


#if __name__=='__main__':
