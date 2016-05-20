#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
"""Module for testing the pxeswitch command.

This may have issues being tested somewhere that the command actually works...
"""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestPxeswitch(TestBrokerCommand):
    """Simplified tests for the pxeswitch command.

    Since we can't actually run aii-installfe against imaginary hosts, the
    unittest.conf file specifies /bin/echo as the command to use.  These
    tests just check that the available parameters are passed through
    correctly.

    """

    def testinstallunittest00(self):
        command = "pxeswitch --hostname unittest00.one-nyp.ms.com --install"
        # This relies on the tests being configured to use /bin/echo instead
        # of the actual aii-installfe.  It would be better to have a fake
        # version of aii-installfe that returned output closer to the real
        # one.
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--installlist", command)
        self.matchoutput(err, "--configurelist", command)
        self.matchclean(err, "--status", command)
        self.matchclean(err, "--rescue", command)
        self.matchclean(err, "--boot", command)
        self.matchclean(err, "--firmware", command)
        self.matchclean(err, "--livecd", command)
        ssh = self.config.lookup_tool("ssh")
        if ssh[0] == '/':
            self.matchoutput(err, "--sshdir %s" % os.path.dirname(ssh), command)
        user = self.config.get("broker", "installfe_user")
        self.matchoutput(err,
                         "--servers %s@infra1.aqd-unittest.ms.com" % user,
                         command)

    def testinstallunittest00noconf(self):
        command = ["pxeswitch", "--hostname", "unittest00.one-nyp.ms.com",
                   "--install", "--noconfigure"]
        err = self.statustest(command)
        self.matchoutput(err, "--installlist", command)
        self.matchclean(err, "--configure", command)
        self.matchclean(err, "--status", command)
        self.matchclean(err, "--rescue", command)
        self.matchclean(err, "--boot", command)
        self.matchclean(err, "--firmware", command)
        self.matchclean(err, "--livecd", command)
        ssh = self.config.lookup_tool("ssh")
        if ssh[0] == '/':
            self.matchoutput(err, "--sshdir %s" % os.path.dirname(ssh), command)
        user = self.config.get("broker", "installfe_user")
        self.matchoutput(err,
                         "--servers %s@infra1.aqd-unittest.ms.com" % user,
                         command)

    def testinstallunittest02(self):
        command = ["pxeswitch", "--hostname", "unittest02.one-nyp.ms.com",
                   "--install"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "You should change the build status before "
                         "switching the PXE link to install.", command)

    def testlocalbootunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --localboot"
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--bootlist", command)

    def teststatusunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --status"
        err = self.statustest(command.split(" "))
        self.matchclean(err, "--configure", command)
        self.matchoutput(err, "--statuslist", command)

    def testfirmwareunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --firmware"
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--firmwarelist", command)

    def testconfigureunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com"
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)

    def testblindbuildunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --blindbuild"
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--livecdlist", command)

    def testrescueunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --rescue"
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--rescuelist", command)

    def testconfigurelist(self):
        hosts = ["uNitTest02.one-nyp.ms.com",
                 "unittest00.One-Nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s" % scratchfile
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        # We would like to test more of the output... we need something
        # special for aii-shellfe however...

    def testconfigurelisterror1(self):
        hosts = ["not-an-fqdn",
                 "host-does-not-exist.ms.com",
                 "host.domain-does-not-exist.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s --configure" % scratchfile
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Invalid hosts in list:", command)
        self.matchoutput(out, "not-an-fqdn: Not an FQDN.", command)
        self.matchoutput(out,
                         "Host host-does-not-exist.ms.com not found.",
                         command)
        self.matchoutput(out,
                         "Host host.domain-does-not-exist.ms.com not found.",
                         command)
        self.matchoutput(out,
                         "DNS Domain domain-does-not-exist.ms.com not found.",
                         command)

    def testconfigurelisterror2(self):
        hosts = [self.aurora_without_node + ".ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s --configure" % scratchfile
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Invalid hosts in list:", command)
        self.matchoutput(out, "Host %s.ms.com has no bootserver." %
                         self.aurora_without_node, command)

    def testinstallisterror(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "unittest00.one-nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --install --list %s" % scratchfile
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "unittest02.one-nyp.ms.com: You should "
                         "change the build status before switching the "
                         "PXE link to install.", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testblindbuildlist(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "unittest00.one-nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s --blindbuild" % scratchfile
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--livecdlist", command)

    def testrescuelist(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "unittest00.one-nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s --rescue" % scratchfile
        err = self.statustest(command.split(" "))
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--rescuelist", command)

    def testrescuelistnoconf(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "unittest00.one-nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = "pxeswitch --list %s --rescue --noconfigure" % scratchfile
        err = self.statustest(command.split(" "))
        self.matchclean(err, "--configurelist", command)
        self.matchoutput(err, "--rescuelist", command)

# --configure is the default now, so this is no longer a conflict
#    def teststatusconflictconfigure(self):
#        command = ["pxeswitch", "--hostname=unittest02.one-nyp.ms.com",
#                   "--status", "--configure"]
#        self.badoptiontest(command)

    def teststatusconflictinstall(self):
        command = ["pxeswitch", "--hostname=unittest02.one-nyp.ms.com",
                   "--status", "--install"]
        self.badoptiontest(command)

    def teststatusconflictinstalllist(self):
        command = ["pxeswitch", "--list=does-not-actually-exist",
                   "--status", "--install"]
        self.badoptiontest(command)

    def testinstallconflictfirmware(self):
        command = ["pxeswitch", "--hostname=unittest02.one-nyp.ms.com",
                   "--firmware", "--install"]
        self.badoptiontest(command)

    def testallowconfigureinstall(self):
        command = ["pxeswitch", "--hostname=unittest00.one-nyp.ms.com",
                   "--configure", "--install"]
        err = self.statustest(command)
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--installlist", command)
        self.matchclean(err, "--firmware", command)

    def testallowconfigureblindbuildlist(self):
        hosts = ["unittest02.one-nyp.ms.com",
                 "unittest00.one-nyp.ms.com"]
        scratchfile = self.writescratch("pxeswitchlist", "\n".join(hosts))
        command = ["pxeswitch", "--list", scratchfile,
                   "--configure", "--blindbuild"]
        err = self.statustest(command)
        self.matchoutput(err, "--configurelist", command)
        self.matchoutput(err, "--livecdlist", command)
        self.matchclean(err, "--firmware", command)

    def testfailoverpxeswitchlimitlist(self):
        hostlimit = self.config.getint("broker", "pxeswitch_max_list_size")
        hosts = []
        for i in range(1, 20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com" % i)
        scratchfile = self.writescratch("pxeswitchlistlimit", "\n".join(hosts))
        command = ["pxeswitch", "--list", scratchfile,
                   "--configure", "--blindbuild"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPxeswitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
