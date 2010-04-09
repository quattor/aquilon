#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

from __future__ import with_statement

import os
import sys
import unittest
from tempfile import NamedTemporaryFile

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestPxeswitch(TestBrokerCommand):
    """Simplified tests for the pxeswitch command.

    Since we can't actually run aii-installfe against imaginary hosts, the
    unittest.conf file specifies /bin/echo as the command to use.  These
    tests just check that the available parameters are passed through
    correctly.

    """

    def testinstallunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --install"
        # This relies on the tests being configured to use /bin/echo instead
        # of the actual aii-installfe.  It would be better to have a fake
        # version of aii-installfe that returned output closer to the real
        # one.
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--install", command)
        sshdir = self.config.get("broker", "installfe_sshdir")
        self.matchoutput(err, "--sshdir %s" % sshdir, command)
        user = self.config.get("broker", "installfe_user")
        self.matchoutput(err,
                         "--servers %s@server9.aqd-unittest.ms.com" % user,
                         command)

    def testlocalbootunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --localboot"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--boot", command)

    def teststatusunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --status"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--status", command)

    def testfirmwareunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --firmware"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--firmware", command)

    def testconfigureunittest02(self):
        command = "pxeswitch --hostname unittest02.one-nyp.ms.com --configure"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "--configure", command)

    def testconfigurelist(self):
        with NamedTemporaryFile() as f:
            f.writelines(["unittest02.one-nyp.ms.com\n",
                          "unittest00.one-nyp.ms.com\n"])
            f.flush()
            command = "pxeswitch --list %s --configure" % f.name
            (out, err) = self.successtest(command.split(" "))
            self.matchoutput(err, "--configure", command)
            # We would like to test more of the output... we need something
            # special for aii-shellfe however...


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPxeswitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

