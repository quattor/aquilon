#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Module for testing the add aurora host command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddAuroraHost(TestBrokerCommand):
    linux_version_prev = None

    @classmethod
    def setUpClass(cls):
        super(TestAddAuroraHost, cls).setUpClass()
        cls.linux_version_prev = cls.config.get("unittest", "linux_version_prev")

    def test_100_add_aurora_with_node(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_with_node)
        self.noouttest(["add", "aurora", "host",
                        "--osname", "linux", "--osversion", self.linux_version_prev,
                        "--hostname", self.aurora_with_node, "--buildstatus", "build"])
        self.dsdb_verify()

    def test_110_verify_add_aurora_with_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Machine: %s" % self.aurora_with_node, command)
        self.matchoutput(out, "Model Type: aurora_node", command)
        self.matchoutput(out, "Chassis: oy604c2.ms.com", command)
        self.matchoutput(out, "Rack: oy604", command)
        self.matchoutput(out, "Row: b", command)
        self.matchoutput(out, "Column: 04", command)
        self.matchoutput(out, "Slot: 6", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: %s" % self.config.get("archetype_aurora",
                                                             "default_domain"),
                         command)
        self.matchoutput(out, "Status: build", command)

        # Rack data from DSDB supported.
        self.matchoutput(out, "Row: b", command)
        self.matchoutput(out, "Column: 04", command)

    def test_120_verify_add_aurora_chassis_grn(self):
        command = ["show_chassis", "--chassis", "oy604c2.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Primary Name: oy604c2.ms.com",
                         command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/aqd", command)

    def test_130_verify_add_aurora_with_node_modify(self):
        command = "change status --hostname %s.ms.com --buildstatus ready" % self.aurora_with_node
        self.successtest(command.split(" "))
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Status: ready", command)

    def test_160_show_host_proto(self):
        fqdn = self.aurora_with_node
        if not fqdn.endswith(".ms.com"):
            fqdn = "%s.ms.com" % fqdn
        command = ["show_host", "--hostname", fqdn, "--format=proto"]
        host = self.protobuftest(command, expect=1)[0]
        self.assertEqual(host.fqdn, fqdn)
        self.assertEqual(host.ip, "")

    def test_200_add_aurora_without_node(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_without_node)
        command = ["add", "aurora", "host",
                        "--osname", "linux", "--osversion", self.linux_version_prev,
                        "--hostname", self.aurora_without_node] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()

    def test_210_verify_add_aurora_without_node(self):
        command = "show host --hostname %s.ms.com" % self.aurora_without_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: %s" % self.aurora_without_node,
                         command)
        self.matchoutput(out, "Machine: ", command)
        self.matchoutput(out, "Model Type: aurora_node", command)
        self.matchoutput(out, "Building: ", command)
        self.matchoutput(out, "Archetype: aurora", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: %s" % self.config.get("archetype_aurora",
                                                             "default_domain"),
                         command)
        self.matchoutput(out, "Status: ready", command)

    def test_220_cat_machine(self):
        command = "cat --machine %s" % self.aurora_without_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template "
                         "machine/americas/ut/None/%s" % self.aurora_without_node,
                         command)

    def test_300_dsdb_missing(self):
        self.dsdb_expect("show_host -host_name not-in-dsdb", fail=True)
        command = ["add", "aurora", "host", "--hostname", "not-in-dsdb",
                   "--osname", "linux", "--osversion", self.linux_version_prev]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not find not-in-dsdb in DSDB", command)
        self.dsdb_verify()

    def test_310_dsdb_rack_missing(self):
        self.dsdb_expect("show_host -host_name %s" % self.aurora_without_rack)
        command = ["add", "aurora", "host",
                   "--hostname", self.aurora_without_rack,
                   "--osname", "linux", "--osversion", self.linux_version_prev] + self.valid_just_tcm
        out = self.statustest(command)
        self.matchoutput(out, "Rack oy605 not defined in DSDB.", command)
        self.dsdb_verify()

    def test_320_verify_dsdb_rack_missing(self):
        command = "show host --hostname %s.ms.com" % self.aurora_with_node
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: oy", command)

    def test_400_add_nyaqd1(self):
        self.dsdb_expect("show_host -host_name nyaqd1")
        command = ["add", "aurora", "host", "--hostname", "nyaqd1",
                        "--osname", "linux",
                        "--osversion", self.linux_version_prev] + self.valid_just_tcm
        self.noouttest(command)
        self.dsdb_verify()

    def test_410_verify_add_nyaqd1(self):
        command = "show host --hostname nyaqd1.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ny00l4as01", command)
        self.matchoutput(out, "Model Type: aurora_node", command)
        self.matchoutput(out, "Primary Name: nyaqd1.ms.com", command)

    def test_420_show_machine(self):
        command = "search machine --model aurora_model --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ny00l4as01", command)
        self.matchoutput(out, "Model Type: aurora_node", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddAuroraHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
