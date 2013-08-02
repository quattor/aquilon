#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestNetworkConstraints(TestBrokerCommand):
    def test_100_add_testnet(self):
        self.net.allocate_network(self, "bunker_mismatch1", 24, "unknown",
                                  "building", "ut")
        self.net.allocate_network(self, "bunker_mismatch2", 24, "unknown",
                                  "bunker", "bucket1.ut")

    def test_110_mismatch_1(self):
        # Rack is bunkerized, network is not
        net = self.net["bunker_mismatch1"]
        ip = net.usable[0]
        self.dsdb_expect_add("mismatch1.aqd-unittest.ms.com", ip,
                             "eth0_bunkertest",
                             primary="aquilon61.aqd-unittest.ms.com")
        command = ["add_interface_address",
                   "--machine", "aquilon61.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest",
                   "--ip", ip, "--fqdn", "mismatch1.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Bunker violation: rack ut9 is inside bunker "
                         "bucket2.ut, but network bunker_mismatch1 is not "
                         "bunkerized.",
                         command)
        self.dsdb_verify()

    def test_120_mismatch_2(self):
        # Rack and network has different bunkers
        net = self.net["bunker_mismatch2"]
        ip = net.usable[0]
        self.dsdb_expect_add("mismatch2.aqd-unittest.ms.com", ip,
                             "eth0_bunkertest",
                             primary="aquilon62.aqd-unittest.ms.com")
        command = ["add_interface_address",
                   "--machine", "aquilon62.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest",
                   "--ip", ip, "--fqdn", "mismatch2.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Bunker violation: rack ut9 is inside bunker "
                         "bucket2.ut, but network bunker_mismatch2 is inside "
                         "bunker bucket1.ut.",
                         command)
        self.dsdb_verify()

    def test_130_mismatch_3(self):
        # Network is bunkerized, rack is not
        net = self.net["bunker_mismatch2"]
        ip = net.usable[1]
        self.dsdb_expect_add("mismatch3.aqd-unittest.ms.com", ip,
                             "eth0_bunkertest",
                             primary="server9.aqd-unittest.ms.com")
        command = ["add_interface_address",
                   "--machine", "server9.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest",
                   "--ip", net.usable[1],
                   "--fqdn", "mismatch3.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Bunker violation: network bunker_mismatch2 is "
                         "inside bunker bucket1.ut, but rack ut8 is not inside "
                         "a bunker.",
                         command)
        self.dsdb_verify()

    def test_200_show_bunker_violations(self):
        command = ["show_bunker_violations"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"Warning: Rack ut8 is not part of a bunker, but it "
                          r"uses bunkerized networks:\s*"
                          r"BUCKET1: server9\.aqd-unittest\.ms\.com/eth0\s*"
                          r"BUCKET2: server9\.aqd-unittest\.ms\.com/eth0",
                          command)
        self.matchoutput(out, "aq update rack --rack np7 --building np",
                         command)
        self.searchoutput(out,
                          r"Warning: Rack ut9 is part of bunker bucket2.ut, but "
                          r"also has networks from:\s*"
                          r"\(No bucket\): aquilon61\.aqd-unittest\.ms\.com/eth0\s*"
                          r"BUCKET1: aquilon62\.aqd-unittest\.ms\.com/eth0",
                          command)

    def test_300_mismatch1_cleanup(self):
        net = self.net["bunker_mismatch1"]
        ip = net.usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del_interface_address",
                   "--machine", "aquilon61.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_300_mismatch2_cleanup(self):
        net = self.net["bunker_mismatch2"]
        ip = net.usable[0]
        self.dsdb_expect_delete(ip)
        command = ["del_interface_address",
                   "--machine", "aquilon62.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_300_mismatch3_cleanup(self):
        net = self.net["bunker_mismatch2"]
        ip = net.usable[1]
        self.dsdb_expect_delete(ip)
        command = ["del_interface_address",
                   "--machine", "server9.aqd-unittest.ms.com",
                   "--interface", "eth0", "--label", "bunkertest"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_310_network_cleanup(self):
        self.net.dispose_network(self, "bunker_mismatch1")
        self.net.dispose_network(self, "bunker_mismatch2")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestNetworkConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
