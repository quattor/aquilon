#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestManageList(TestBrokerCommand):

    def test_100_forced_manage_list(self):
        user = self.config.get("unittest", "user")
        hosts = ["aquilon65.aqd-unittest.ms.com\n",
                 "aquilon66.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest1" % user, "--force"])

    def test_101_verify_forced_manage_list(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname aquilon65.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon65.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % user, command)
        command = "show host --hostname aquilon66.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon66.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % user, command)

    def test_102_manage_list(self):
        user = self.config.get("unittest", "user")
        hosts = ["aquilon65.aqd-unittest.ms.com\n",
                 "aquilon66.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest2" % user])

    def test_103_verify_manage_list(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname aquilon65.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aquilon65.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % user, command)
        self.verify_buildfiles("managetest1", "aquilon65.aqd-unittest.ms.com",
                               want_exist=False)
        command = "show host --hostname aquilon66.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: aquilon66.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest2" % user, command)

    def test_104_fail_manage_list_nomanage(self):
        hosts = ["unittest02.one-nyp.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        command = ["manage", "--list", scratchfile, "--domain", "nomanage"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Managing hosts to domain nomanage is "
                         "not allowed.", command)

    def test_105_fail_manage_empty_list(self):
        user = self.config.get("unittest", "user")
        hosts = []
        scratchfile = self.writescratch("managelist", "".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Empty list.", command)

    def test_106_fail_manage_invalid_list(self):
        user = self.config.get("unittest", "user")
        hosts = ["thishostdoesnotexist.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Invalid hosts in list:\n%s" % hosts[0].rstrip("\n"),
                         command)

    def test_107_fail_manage_list_domain(self):
        user = self.config.get("unittest", "user")
        hosts = ["server2.aqd-unittest.ms.com\n",
                 "unittest02.one-nyp.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "All hosts must be in the same domain or sandbox",
                         command)

    def test_108_fail_manage_list_cluster(self):
        user = self.config.get("unittest", "user")
        hosts = ["evh1.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        command = ["manage", "--list", scratchfile,
                   "--sandbox", "%s/changetest1" % user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cluster nodes must be managed at the cluster level",
                         command)

    def test_109_manage_list_buildfiles(self):
        self.verify_buildfiles("unittest", "unittest17.aqd-unittest.ms.com",
                               want_exist=True)
        user = self.config.get("unittest", "user")
        hosts = ["unittest17.aqd-unittest.ms.com\n"]
        scratchfile = self.writescratch("managelist", "".join(hosts))
        self.noouttest(["manage", "--list", scratchfile,
                        "--sandbox", "%s/managetest1" % user, "--force"])
        self.verify_buildfiles("unittest", "unittest17.aqd-unittest.ms.com",
                               want_exist=False)

    def test_110_verify_manage_list_buildfiles(self):
        user = self.config.get("unittest", "user")
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % user, command)
        command = "show host --hostname unittest17.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest17.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Sandbox: %s/managetest1" % user, command)

    def test_120_fail_overlimit_manage_list(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "manage_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" % i)
        scratchfile = self.writescratch("managelistlimit", "".join(hosts))
        command = ["manage", "--list", scratchfile, "--sandbox",
                   "%s/changetest1" % user, "--force"]
        out = self.badrequesttest(command)
        self.matchoutput(out,"The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManageList)
    unittest.TextTestRunner(verbosity=2).run(suite)
