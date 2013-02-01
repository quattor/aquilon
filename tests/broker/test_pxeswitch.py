#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the pxeswitch command.

This may have issues being tested somewhere that the command actually works...
"""


import unittest
from tempfile import NamedTemporaryFile

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--install", command)
        self.matchoutput(err, "--configure", command)
        self.matchclean(err, "--status", command)
        self.matchclean(err, "--rescue", command)
        self.matchclean(err, "--boot", command)
        self.matchclean(err, "--firmware", command)
        self.matchclean(err, "--livecd", command)
        sshdir = self.config.get("broker", "installfe_sshdir")
        self.matchoutput(err, "--sshdir %s" % sshdir, command)
        user = self.config.get("broker", "installfe_user")
        self.matchoutput(err,
                         "--servers %s@server9.aqd-unittest.ms.com" % user,
                         command)

    def testinstallunittest00noconf(self):
        command = ["pxeswitch", "--hostname", "unittest00.one-nyp.ms.com",
                   "--install", "--noconfigure"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "--install", command)
        self.matchclean(err, "--configure", command)
        self.matchclean(err, "--status", command)
        self.matchclean(err, "--rescue", command)
        self.matchclean(err, "--boot", command)
        self.matchclean(err, "--firmware", command)
        self.matchclean(err, "--livecd", command)
        sshdir = self.config.get("broker", "installfe_sshdir")
        self.matchoutput(err, "--sshdir %s" % sshdir, command)
        user = self.config.get("broker", "installfe_user")
        self.matchoutput(err,
                         "--servers %s@server9.aqd-unittest.ms.com" % user,
                         command)

    def testinstallunittest02(self):
        command = ["pxeswitch", "--hostname", "unittest02.one-nyp.ms.com",
                   "--install"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "You should change the build status before "
                         "switching the PXE link to install.", command)

    def testlocalbootunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --localboot"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)
        self.matchoutput(err, "--boot", command)

    def teststatusunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --status"
        (out, err) = self.successtest(command.split(" "))
        self.matchclean(err, "--configure", command)
        self.matchoutput(err, "--status", command)

    def testfirmwareunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --firmware"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)
        self.matchoutput(err, "--firmware", command)

    def testconfigureunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)

    def testblindbuildunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --blindbuild"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)
        self.matchoutput(err, "--livecd", command)

    def testrescueunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --rescue"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)
        self.matchoutput(err, "--rescue", command)

    def testconfigurelist(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s" % f.name
            (out, err) = self.successtest(command.split(" "))
            self.matchoutput(err, "--configurelist", command)
            # We would like to test more of the output... we need something
            # special for aii-shellfe however...

    def testconfigurelisterror(self):
        with NamedTemporaryFile() as f:
            f.writelines(["host-does-not-exist.ms.com\n",
                          "host.domain-does-not-exist.ms.com\n",
                          "pissp1.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s --configure" % f.name
            out = self.badrequesttest(command.split(" "))
            self.matchoutput(out, "Invalid hosts in list:", command)
            self.matchoutput(out, "host-does-not-exist.ms.com: Host "
                             "host-does-not-exist.ms.com not found.",
                             command)
            self.matchoutput(out, "domain-does-not-exist.ms.com: DNS Domain "
                             "domain-does-not-exist.ms.com not found.",
                             command)
            self.matchoutput(out, "pissp1.ms.com: Host has no bootserver.",
                             command)

    def testinstallisterror(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --install --list %s" % f.name
            out = self.badrequesttest(command.split(" "))
            self.matchoutput(out, "unittest02.one-nyp.ms.com: You should "
                             "change the build status before switching the "
                             "PXE link to install.", command)
            self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testblindbuildlist(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s --blindbuild" % f.name
            (out, err) = self.successtest(command.split(" "))
            self.matchoutput(err, "--configurelist", command)
            self.matchoutput(err, "--livecdlist", command)

    def testrescuelist(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s --rescue" % f.name
            (out, err) = self.successtest(command.split(" "))
            self.matchoutput(err, "--configurelist", command)
            self.matchoutput(err, "--rescuelist", command)

    def testrescuelistnoconf(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s --rescue --noconfigure" % f.name
            (out, err) = self.successtest(command.split(" "))
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
        (out, err) = self.successtest(command)
        self.matchoutput(err, "--configure unittest00.one-nyp.ms.com", command)
        self.matchoutput(err, "--install unittest00.one-nyp.ms.com", command)
        self.matchclean(err, "--firmware", command)

    def testallowconfigureblindbuildlist(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = ["pxeswitch", "--list", f.name,
                       "--configure", "--blindbuild"]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "--configurelist", command)
            self.matchoutput(err, "--livecdlist", command)
            self.matchclean(err, "--firmware", command)

    def testfailoverpxeswitchlimitlist(self):
        user = self.config.get("unittest", "user")
        hostlimit = self.config.getint("broker", "pxeswitch_max_list_size")
        hosts = []
        for i in range(1,20):
            hosts.append("thishostdoesnotexist%d.aqd-unittest.ms.com\n" %i)
        scratchfile = self.writescratch("pxeswitchlistlimit", "".join(hosts))
        command = ["pxeswitch", "--list", scratchfile,
                   "--configure", "--blindbuild"]
        out = self.badrequesttest(command)
        self.matchoutput(out,"The number of hosts in list {0:d} can not be more "
                         "than {1:d}".format(len(hosts), hostlimit), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPxeswitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
