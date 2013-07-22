#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the show machine command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestShowMachine(TestBrokerCommand):
    def testverifyut3c1n3interfacescsv(self):
        command = "show machine --machine ut3c1n3 --format csv"
        out = self.commandtest(command.split(" "))
        net = self.net["unknown0"]
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,eth0,%s,%s" %
                         (net.usable[2].mac, net.usable[2]), command)
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,eth1,%s,%s" %
                         (net.usable[3].mac, net.usable[3]), command)
        self.matchoutput(out,
                         "ut3c1n3,ut3,ut,ibm,hs21-8853l5u,KPDZ406,bmc,%s,%s" %
                         (net.usable[4].mac, net.usable[4]), command)

    def testrejectfqdn(self):
        command = "show machine --machine unittest00.one-nyp.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Illegal hardware label", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
