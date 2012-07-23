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
"""Module for testing the add reboot_schedule command."""

import unittest
import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRebootSchedule(TestBrokerCommand):

    def test_100_nonexistent(self):
        command = ["show_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)

    def test_110_add_schedule(self):
        # devaq add_reboot_schedule --hostname aquilon07.one-nyp.ms.com
        # --week 1,2,3,4,5 --day Sun --time 06:00
        command = ["add_reboot_schedule",
                   "--week=all", "--day=Sun", "--time=08:00",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_115_make(self):
        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_120_show_reboot_schedule(self):
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

    def test_120_cat_resource(self):
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

    def test_120_cat_host(self):
        command = ["cat", "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         '"system/resources/reboot_schedule" = '
                         'append(create("resource/host/server1.aqd-unittest.ms.com/reboot_schedule/reboot_schedule/config"))',
                         command)

    def test_120_show_all(self):
        command = ["show_reboot_schedule", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "RebootSchedule: reboot_schedule", command)

    def test_120_show_host(self):
        command = ["show_host", "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "RebootSchedule: reboot_schedule", command)

    def test_120_show_host_proto(self):
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
                self.failUnlessEqual(resource.reboot_schedule.week, "All")
                self.failUnlessEqual(resource.reboot_schedule.day, "Sun")
                self.failUnlessEqual(resource.reboot_schedule.time, "08:00")
        self.assertTrue(found,
                        "Reboot schedule not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join(["%s %s" % (res.type, res.name) for res in
                                              host.resources]))

    def test_200_add_existing(self):
        command = ["add_reboot_schedule",
                   "--week=all", "--day=Sun", "--time=08:00",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_200_cat_notfound(self):
        command = ["cat", "--reboot_schedule=schedule-does-not-exist",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.notfoundtest(command)

    def test_300_del_reboot_schedule(self):
        plenary = self.plenary_name("resource", "host",
                                    "server1.aqd-unittest.ms.com",
                                    "reboot_schedule", "reboot_schedule",
                                    "config")
        self.failUnless(os.path.exists(plenary),
                        "Pleanry '%s' does not exist" % plenary)

        command = ["del_reboot_schedule",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        dir = os.path.dirname(plenary)
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    def test_310_verify_del(self):
        command = ["show_host", "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "reboot_schedule", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRebootSchedule)
    unittest.TextTestRunner(verbosity=2).run(suite)
