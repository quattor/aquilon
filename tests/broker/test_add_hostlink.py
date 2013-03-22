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
"""Module for testing the add hostlink command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddHostlink(TestBrokerCommand):

    def test_00_basic_hostlink(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--comments=testing"]
        self.successtest(command)

        command = ["show_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)
        self.matchoutput(out, "Comments: testing", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Target Path: /var/spool/hostlinks/app1", command)
        self.matchoutput(out, "Owner: user1", command)

    def test_10_addexisting(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_15_notfound(self):
        command = "show hostlink --hostlink app-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_30_checkhost(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        hostlinkfound = False
        for resource in host.resources:
            if resource.name == "app1" and resource.type == "hostlink":
                # there is not yet a hostlink protobuf definition so just
                # check that it is found
                hostlinkfound = True
        self.assertTrue(hostlinkfound,
                        "Hostlink resource not found in protocol output")

        command = ["cat", "--generate",
                   "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/hostlink" = append(create("resource/host/server1.aqd-unittest.ms.com/hostlink/app1/config"))', command)

        command = ["del_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHostlink)
    unittest.TextTestRunner(verbosity=2).run(suite)
