#!/usr/bin/env python2.6
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
"""Module for testing the add reboot_schedule command."""

import unittest
import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRebootSchedule(TestBrokerCommand):

    def test_00_basic_reboot_schedule(self):
        command = ["show_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)

        # devaq add_reboot_schedule --hostname aquilon07.one-nyp.ms.com
        # --week 1,2,3,4,5 --day Sun --time 06:00
        command = ["add_reboot_schedule",
                   "--week=all", "--day=Sun", "--time=08:00",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["show_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootSchedule: reboot_schedule",
                         command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Week: All", command)
        self.matchoutput(out, "Day: Sun", command)
        self.matchoutput(out, "Time: 08:00", command)

        command = ["cat", "--reboot_schedule=reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template resource"
                         "/host/server1.aqd-unittest.ms.com"
                         "/reboot_schedule/reboot_schedule/config;",
                         command)
        self.matchoutput(out, "\"name\" = \"reboot_schedule\";", command)
        self.matchoutput(out, "\"time\" = \"08:00\";", command)
        self.matchoutput(out, "\"week\" = \"All\"", command)
        self.matchoutput(out, "\"day\" = \"Sun\"", command)

        command = ["cat", "--reboot_schedule=reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--generate"]
        newout = self.commandtest(command)
        self.assertEqual(out, newout)

        command = ["show_reboot_schedule", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootSchedule: reboot_schedule", command)

    def test_11_addexisting(self):
        command = ["add_reboot_schedule",
                   "--week=all", "--day=Sun", "--time=08:00",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfoundresource(self):
        command = ["cat", "--reboot_schedule=schedule-does-not-exist",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_30_checkthehost(self):
        command = ["show_host", "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "RebootSchedule: reboot_schedule", command)

        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.successtest(command)

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/resources/reboot_schedule" = '
                         'append(create("resource/host/server1.aqd-unittest.ms.com/reboot_schedule/reboot_schedule/config"))',
                         command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        found = False
        for resource in host.resources:
            if resource.name == "reboot_schedule" and \
               resource.type == "reboot_schedule":
                found = True
        self.assertTrue(found, "No reboot_schedule found in host protobuf.")

    def test_del_reboot_schedule(self):
        command = ["del_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_verify_reboot_schedule_plenary(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "resource", "host", "server1.aqd-unittest.ms.com",
                           "reboot_schedule")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRebootSchedule)
    unittest.TextTestRunner(verbosity=2).run(suite)
