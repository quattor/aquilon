#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the add reboot_intervention command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from datetime import datetime, timedelta

from brokertest import TestBrokerCommand

EXPIRY = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
EXPIRY = EXPIRY.isoformat().replace("T", " ")


class TestAddRebootIntervention(TestBrokerCommand):

    def test_00_basic_reboot_intervention(self):
        command = ["show_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)

        command = ["add_reboot_schedule",
                   "--week=all", "--day=Sun", "--time=08:00",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_reboot_intervention",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)

        command = ["add_reboot_intervention", "--expiry", EXPIRY,
                   "--justification=test",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_reboot_intervention",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootIntervention: reboot_intervention",
                         command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Start: ", command)
        self.matchoutput(out, "Expiry: ", command)

        command = ["cat", "--reboot_intervention=reboot_intervention",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template resource"
                         "/host/server1.aqd-unittest.ms.com"
                         "/reboot_iv/reboot_intervention/config;",
                         command)
        self.matchoutput(out, "\"name\" = \"reboot_intervention\";", command)
        self.matchoutput(out, "\"start\" =", command)
        self.matchoutput(out, "\"expiry\" =", command)

        command = ["cat", "--reboot_intervention=reboot_intervention",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--generate"]
        newout = self.commandtest(command)
        self.assertEqual(out, newout)

        command = ["show_reboot_intervention", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootIntervention: reboot_intervention",
                         command)

    def test_11_addexisting(self):
        # FIXME: this fails if the test is run on Sunday
        command = ["add_reboot_intervention", "--expiry=Sun",
                   "--justification=test",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfoundri(self):
        command = ["cat", "--reboot_intervention=ri-does-not-exist",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_30_checkthehost(self):
        command = ["show_host", "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootIntervention", command)

        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.successtest(command)

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/resources/reboot_iv" = '
                         'append(create("resource/host/server1.aqd-unittest.ms.com/reboot_iv/reboot_intervention/config"))',
                         command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        found = False
        for resource in host.resources:
            if resource.name == "reboot_intervention" and \
               resource.type == "reboot_iv":
                found = True
        self.assertTrue(found, "No reboot_iv found in host protobuf.")

    def test_del_reboot_intervention(self):
        command = ["del_reboot_intervention",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)
        command = ["del_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestAddRebootIntervention)
    unittest.TextTestRunner(verbosity=2).run(suite)
