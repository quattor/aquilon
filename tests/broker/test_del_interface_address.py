#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
"""Module for testing the del interface address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelInterfaceAddress(TestBrokerCommand):

    def testdelkeepdns(self):
        ip = self.net["zebra_eth1"].usable[0]
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add("unittest20-e1.aqd-unittest.ms.com", ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--ip", ip, "--keep_dns"]
        self.noouttest(command)
        self.dsdb_verify()

    def testrejectunknownip(self):
        ip = self.net["unknown0"].usable[10]
        command = ["del", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth1", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest00.one-nyp.ms.com "
                         "does not have IP address %s assigned to it." % ip,
                         command)

    def testrejectprimaryip(self):
        ip = self.net["unknown0"].usable[2]
        command = ["del", "interface", "address", "--machine", "ut3c1n3",
                   "--interface", "eth0", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The primary IP address of a hardware entity "
                         "cannot be removed.",
                         command)

    def testbadmachine(self):
        command = ["del", "interface", "address", "--machine", "no-such-machine",
                   "--interface", "eth0", "--ip", "192.168.0.1"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Machine no-such-machine not found.", command)

    def testverifykeepdns(self):
        command = ["search", "dns",
                   "--fqdn", "unittest20-e1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unittest20-e1.aqd-unittest.ms.com", command)

    def testdelbylabel(self):
        ip = self.net["zebra_eth1"].usable[3]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e1"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelbylabelagain(self):
        ip = self.net["zebra_eth1"].usable[3]
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth1", "--label", "e1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Interface eth1 of machine unittest20.aqd-unittest.ms.com "
                         "does not have an address with label e1.",
                         command)

    def testdelunittest20e0(self):
        ip = self.net["zebra_eth0"].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address", "--machine", "ut3c5n2",
                   "--interface", "eth0", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyunittest20(self):
        ip = self.net["zebra_vip"].usable[2]
        command = ["cat", "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--data"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"system/resources/service_address" = '
                          r'append\(create\("resource/host/unittest20.aqd-unittest.ms.com/service_address/hostname/config"\)\);',
                          command)
        self.matchclean(out, "aliases", command)
        self.matchclean(out, "zebra2", command)
        self.matchclean(out, "zebra3", command)

    def testdelunittest25utcolo(self):
        net = self.net["unknown1"]
        ip = net[4]
        command = ["del", "interface", "address",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--interface", "eth1", "--ip", ip,
                   "--network_environment", "utcolo"]
        self.noouttest(command)
        # External addresses should not affect DSDB
        self.dsdb_verify(empty=True)

        ip = net[5]
        command = ["del", "interface", "address",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--interface", "eth2", "--ip", ip,
                   "--network_environment", "utcolo"]
        self.noouttest(command)
        # External addresses should not affect DSDB
        self.dsdb_verify(empty=True)

    def testdelunittest26(self):
        ip = self.net["routing1"].usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address",
                   "--machine", "unittest26.aqd-unittest.ms.com",
                   "--interface", "eth1", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelut3gd1r04vlan220(self):
        ip = self.net["tor_net_12"].usable[1]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "vlan220", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelut3gd1r04vlan220hsrp(self):
        ip = self.net["tor_net_12"].usable[2]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "vlan220", "--label", "hsrp"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelut3gd1r04loop0(self):
        ip = self.net["autopg1"][0]
        self.dsdb_expect_delete(ip)
        command = ["del", "interface", "address",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--interface", "loop0", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterfaceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
