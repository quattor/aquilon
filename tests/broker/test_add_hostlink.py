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
"""Module for testing the add hostlink command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddHostlink(TestBrokerCommand):

    def test_100_add_hostlink(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user1",
                   "--comments=testing"]
        self.successtest(command)

    def test_105_make(self):
        command = ["make", "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_110_show_hostlink(self):
        command = ["show_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)
        self.matchoutput(out, "Comments: testing", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Target Path: /var/spool/hostlinks/app1", command)
        self.matchoutput(out, "Owner: user1", command)

    def test_110_show_host(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hostlink: app1", command)

    def test_110_show_host_proto(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        hostlinkfound = False
        for resource in host.resources:
            if resource.name == "app1" and resource.type == "hostlink":
                self.failUnlessEqual(resource.hostlink.target,
                                     "/var/spool/hostlinks/app1")
                self.failUnlessEqual(resource.hostlink.owner_user, "user1")
                self.failUnlessEqual(resource.hostlink.owner_group, "")
                hostlinkfound = True
        self.assertTrue(hostlinkfound,
                        "Hostlink app1 not found in the resources. "
                        "Existing resources: %s" %
                        ", ".join(["%s %s" % (res.type, res.name)
                                   for res in host.resources]))

    def test_110_cat_host(self):
        command = ["cat", "--hostname", "server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/hostlink" = append(create("resource/host/server1.aqd-unittest.ms.com/hostlink/app1/config"))', command)

    def test_200_add_existing(self):
        command = ["add_hostlink", "--hostlink=app1",
                   "--target=/var/spool/hostlinks/app1",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--owner=user2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_200_notfound(self):
        command = "show hostlink --hostlink app-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_300_del_hostlink(self):
        path = ["resource", "host", "server1.aqd-unittest.ms.com",
                "hostlink", "app1", "config"]
        self.check_plenary_exists(*path)

        command = ["del_hostlink", "--hostlink=app1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        self.check_plenary_gone(*path, directory_gone=True)

    def test_310_verify_del(self):
        command = ["show_host", "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Hostlink", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddHostlink)
    unittest.TextTestRunner(verbosity=2).run(suite)
