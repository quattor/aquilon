#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the add allowed_personality commands."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddAllowedPersonality(TestBrokerCommand):

    def test_10_addbadconstraint(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=generic", "--cluster=utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Member host evh1.aqd-unittest.ms.com has personality "
                         "vmhost/vulcan-10g-server-prod, which is incompatible "
                         "with this constraint.",
                         command)

    def test_12_failmissingcluster(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=vulcan-10g-server-prod", "--cluster=does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Cluster does-not-exist not found.",
                         command)

    def test_14_failmissingcluster(self):
        command = ["add_allowed_personality", "--archetype", "vmhost",
                   "--personality=does-not-exist", "--cluster=utecl1"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality does-not-exist, "
                         "archetype vmhost not found.",
                         command)

    def test_15_addconstraint(self):
        self.noouttest(["add_allowed_personality", "--archetype", "vmhost",
                        "--personality=vulcan-10g-server-prod",
                        "--cluster", "utecl1"])
        self.noouttest(["add_allowed_personality", "--archetype", "vmhost",
                        "--personality=generic", "--cluster", "utecl1"])
        self.noouttest(["add_allowed_personality", "--archetype", "esx_cluster",
                        "--personality=vulcan-10g-server-prod",
                        "--metacluster", "utmc1"])

    def test_20_checkconstraint(self):
        command = ["show_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Allowed Personality: vulcan-10g-server-prod Archetype: vmhost", command)
        self.matchoutput(out, "Allowed Personality: generic Archetype: vmhost", command)

        command = ["show_cluster", "--cluster=utecl1", "--format", "proto"]
        cluster = self.protobuftest(command, expect=1)[0]
        self.assertEqual(len(cluster.allowed_personalities), 2)
        self.assertEqual(set(pers.name for pers in
                             cluster.allowed_personalities),
                         set(["generic", "vulcan-10g-server-prod"]))

        command = ["show_metacluster", "--metacluster=utmc1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Allowed Personality: vulcan-10g-server-prod Archetype: esx_cluster",
                         command)

        command = ["show_metacluster", "--metacluster=utmc1", "--format", "proto"]
        mc = self.protobuftest(command, expect=1)[0]
        self.assertEqual(len(mc.allowed_personalities), 1)
        self.assertEqual(mc.allowed_personalities[0].name,
                         "vulcan-10g-server-prod")

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAllowedPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
