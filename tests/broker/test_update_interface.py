#!/usr/bin/env python2.5
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
"""Module for testing the update interface command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestUpdateInterface(TestBrokerCommand):

    def testupdateut3c5n10eth0mac(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[11].mac])

    def testupdateut3c5n10eth0ip(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--ip", self.net.unknown[0].usable[11].ip])

    def testupdateut3c5n10eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--mac", self.net.unknown[0].usable[12].mac,
                        "--ip", self.net.unknown[0].usable[12].ip, "--boot"])

    def testupdateut3c5n10eth2(self):
        self.badrequesttest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def testverifyupdateut3c5n10interfaces(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        # FIXME: This is currently not working, command nees rethinking.
        #self.matchoutput(out, "IP: %s" % self.hostip7, command)
        self.matchoutput(out,
                         "Interface: eth0 %s boot=False" %
                         self.net.unknown[0].usable[11].mac.lower(),
                         command)
        self.matchoutput(out,
                         "Interface: eth1 %s boot=True" %
                         self.net.unknown[0].usable[12].mac.lower(),
                         command)

    def testverifycatut3c5n10interfaces(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         """"cards/nic/eth0/hwaddr" = "%s";""" %
                         self.net.unknown[0].usable[11].mac.upper(),
                         command)
        self.matchclean(out, """"cards/nic/eth0/boot" = true;""", command)
        self.matchoutput(out,
                         """"cards/nic/eth1/hwaddr" = "%s";""" %
                         self.net.unknown[0].usable[12].mac.upper(),
                         command)
        self.matchoutput(out, """"cards/nic/eth1/boot" = true;""", command)


if __name__=='__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
