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
"""Module for testing the add application command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddApplication(TestBrokerCommand):

    def test_00_basic_application(self):
        command = ["add_application", "--application=app1", "--eonid=42",
                   "--host=server1.aqd-unittest.ms.com",
                   "--comments=testing"]
        self.successtest(command)

        command = ["show_application", "--application=app1",
                   "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Application: app1", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "EON id: 42", command)
        self.matchoutput(out, "Comments: testing", command)

    def test_10_addexisting(self):
        command = ["add_application", "--application=app1", "--eonid=43",
                   "--host=server1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfoundfs(self):
        command = "show application --application app-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_30_checkhost(self):
        command = ["show_host", "--host=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Application: app1", command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        for resource in host.resources:
            if resource.name == "app1" and resource.type == "application":
                self.assertEqual(resource.appdata.eonid, 42)

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/application" = append(create("resource/host/server1.aqd-unittest.ms.com/application/app1/config"))', command)

        command = ["del_application", "--application=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddApplication)
    unittest.TextTestRunner(verbosity=2).run(suite)
