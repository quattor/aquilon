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
"""Module for testing using the cluster command to move between clusters."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


# Note, this used to test the rebind_esx_cluster, however I've
# deco'ed that command. I've kept this test here in order to preserve
# the state of all the previous and subsequent tests that assume the
# state of evh1 (it's a tangled web of statefulness going on here!)

class TestRebindESXCluster(TestBrokerCommand):

    # Failure test is in add_virtual_hardware.
    def test_100_rebind_evh1(self):
        self.successtest(["cluster",
                          "--hostname", "evh1.aqd-unittest.ms.com",
                          "--cluster", "utecl2"])

    def test_110_unbind_evh2(self):
        # Let's see if we can put a node back after the cluster size has shrunk
        command = ["uncluster", "--hostname", "evh2.aqd-unittest.ms.com",
                   "--personality", "generic", "--cluster", "utecl1"]
        self.successtest(command)

    def test_111_rebind_evh2(self):
        command = ["cluster", "--hostname", "evh2.aqd-unittest.ms.com",
                   "--personality", "vulcan-1g-desktop-prod",
                   "--cluster", "utecl1"]
        self.successtest(command)

    def test_200_verifyrebindevh1(self):
        command = "show host --hostname evh1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: evh1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Member of ESX Cluster: utecl2", command)

        # FIXME: Also test plenary files.

    def test_200_verify_evh2(self):
        command = ["show", "cluster", "--cluster", "utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Member: evh2.aqd-unittest.ms.com [node_index: 0]",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRebindESXCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
