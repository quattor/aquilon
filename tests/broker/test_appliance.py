#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013,2014  Contributor
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
"""Module for testing the appliance related commands."""

import os
from datetime import datetime

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin
from machinetest import MachineTestMixin
from personalitytest import PersonalityTestMixin


class TestAppliance(VerifyNotificationsMixin, MachineTestMixin,
                    PersonalityTestMixin, TestBrokerCommand):

    cluster = "utecl10"
    vapp = "utvapp0"

    def test_100_add_personality(self):
        # vmhost archetype
        self.create_personality("utappliance", "virt-appliance",
                                grn="grn:/ms/ei/aquilon/aqd")

    def test_110_add_appliance(self):
        command = ["add", "machine", "--machine", self.vapp,
                   "--cluster", self.cluster, "--model", "utva",
                   "--uri", "file:///somepath/to/ovf"]
        self.noouttest(command)

    def test_120_verify_appliance(self):
        command = ["show", "machine", "--machine", self.vapp]
        out = self.commandtest(command)

        self.searchoutput(out, r"URI: file:///somepath/to/ovf", command)

        command = ["cat", "--machine", self.vapp, "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, '"uri" = "file:///somepath/to/ovf";', command)

    def test_150_update_uri(self):
        command = ["update", "machine", "--machine", self.vapp,
                   "--uri", "file:///otherpath/to/ovf"]
        self.noouttest(command)

        command = ["show", "machine", "--machine", self.vapp]
        out = self.commandtest(command)

        self.searchoutput(out, r"URI: file:///otherpath/to/ovf", command)

    def test_200_add_appliance_host_if(self):
        self.noouttest(["add", "interface", "--machine", self.vapp,
                        "--interface", "eth0", "--automac", "--autopg"])

    def test_210_add_appliance_host(self):
        ip = self.net["appliance"].usable[0]
        self.dsdb_expect_add("utva.aqd-unittest.ms.com", ip, "eth0", "00:50:56:01:20:4b")
        command = ["add", "host", "--hostname", "utva.aqd-unittest.ms.com",
                   "--ip", ip,
                   "--machine", self.vapp,
                   "--domain", "unittest", "--buildstatus", "build",
                   "--archetype", "utappliance",
                   "--personality", "virt-appliance",
                   "--osname", "utos", "--osversion", "1.0"]
        self.noouttest(command)
        self.dsdb_verify()

    # TODO do we need this?
    # def test_280_makecluster(self):
    #     command = ["make_cluster", "--cluster=%s" % self.cluster]
    #     (out, err) = self.successtest(command)

    def test_300_del_appl_host(self):
        basetime = datetime.now()
        self.dsdb_expect_delete(self.net["appliance"].usable[0])
        command = ["del", "host", "--hostname", "utva.aqd-unittest.ms.com"]
        self.statustest(command)
        self.wait_notification(basetime, 1)
        self.dsdb_verify()

    def test_310_del_appliance(self):
        command = ["del", "machine", "--machine", self.vapp]
        self.noouttest(command)

    def test_320_del_personality(self):
        command = ["del_personality", "--archetype", "utappliance",
                   "--personality", "virt-appliance"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAppliance)
    unittest.TextTestRunner(verbosity=2).run(suite)
