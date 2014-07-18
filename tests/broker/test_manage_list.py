#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""Module for testing the manage --list command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestManageList(TestBrokerCommand):

    def test_100_forced_manage_list(self):
        hosts = ["aquilon65.aqd-unittest.ms.com",
                 "aquilon66.aqd-unittest.ms.com"]
        for h in hosts:
            self.successtest(["compile", "--hostname", h])
            self.verify_buildfiles("utsandbox", h, want_exist=True)

        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest1" % self.user, "--force"])
        for h in hosts:
            self.verify_buildfiles("utsandbox", h, want_exist=False)
            plen = self.build_profile_name(h, domain="managetest1")
            self.failUnless(os.path.exists(plen), "%s does not exit." % plen)

    def test_101_verify_forced_manage_list(self):
        command = "show host --hostname aquilon65.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon65.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % self.user, command)
        command = "show host --hostname aquilon66.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon66.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % self.user, command)

    def test_102_manage_list(self):
        hosts = ["aquilon65.aqd-unittest.ms.com",
                 "aquilon66.aqd-unittest.ms.com"]
        for h in hosts:
            self.successtest(["compile", "--hostname", h])
            self.verify_buildfiles("managetest1", h, want_exist=True)

        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest2" % self.user])
        for h in hosts:
            self.verify_buildfiles("managetest1", h, want_exist=False)
            plen = self.build_profile_name(h, domain="managetest2")
            self.failUnless(os.path.exists(plen), "%s does not exit." % plen)

    def test_103_verify_manage_list(self):
        command = "show host --hostname aquilon65.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aquilon65.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % self.user, command)
        self.verify_buildfiles("managetest1", "aquilon65.aqd-unittest.ms.com",
                               want_exist=False)
        command = "show host --hostname aquilon66.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon66.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % self.user, command)

    def test_104_fail_manage_list_nomanage(self):
        hosts = ["unittest02.one-nyp.ms.com"]
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        command = ["manage", "--list", scratchfile, "--domain", "nomanage"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Managing objects to domain nomanage is not allowed.",
                         command)

    def test_105_fail_manage_empty_list(self):
        hosts = []
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % self.user]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Empty list.", command)

    def test_106_fail_manage_invalid_list(self):
        hosts = ["thishostdoesnotexist.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % self.user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Invalid hosts in list:\n%s" % hosts[0].rstrip("\n"),
                         command)

    def test_107_fail_manage_list_domain(self):
        hosts = ["server2.aqd-unittest.ms.com",
                 "unittest02.one-nyp.ms.com"]
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % self.user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "All hosts must be in the same domain or sandbox",
                         command)

    def test_108_fail_manage_list_cluster(self):
        hosts = ["evh1.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        command = ["manage", "--list", scratchfile,
                   "--sandbox", "%s/changetest1" % self.user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cluster nodes must be managed at the cluster level",
                         command)

    def test_109_manage_list_buildfiles(self):
        self.verify_buildfiles("unittest", "unittest17.aqd-unittest.ms.com",
                               want_exist=True)
        hosts = ["unittest17.aqd-unittest.ms.com"]
        scratchfile = self.writescratch("managelist", "\n".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest1" % self.user, "--force"])
        self.verify_buildfiles("unittest", "unittest17.aqd-unittest.ms.com",
                               want_exist=False)

    def test_110_verify_manage_list_buildfiles(self):
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % self.user, command)
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % self.user, command)

    def test_120_fail_overlimit_manage_list(self):
        hostlimit = self.config.getint("broker", "manage_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com" % i)
        scratchfile = self.writescratch("managelistlimit", "\n".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % self.user, "--force"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit),
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManageList)
    unittest.TextTestRunner(verbosity=2).run(suite)
