#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUpdateInterface(TestBrokerCommand):

    def testupdateut3c5n10eth0mac(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--mac", self.net.unknown[0].usable[11].mac])

    def testupdateut3c5n10eth0ip(self):
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10",
                        "--ip", self.net.unknown[0].usable[11]])

    def testupdateut3c5n10eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--mac", self.net.unknown[0].usable[12].mac,
                        "--ip", self.net.unknown[0].usable[12], "--boot"])

    def testupdateut3c5n10eth2(self):
        self.notfoundtest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def testupdatebadhost(self):
        # Use host name instead of machine name
        self.notfoundtest(["update", "interface", "--interface", "eth0",
                           "--machine", "unittest02.one-nyp.ms.com"])

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
        #FIX ME: this doesn't really test anything at the moment: needs to be
        #statefully parsing the interface output
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*\);'
                          % self.net.unknown[0].usable[11].mac,
                          command)
        self.searchoutput(out,
                          r'"cards/nic/eth1" = nlist\(\s*'
                          r'"hwaddr", "%s",\s*'
                          r'"boot", true,\s*\);'
                          % self.net.unknown[0].usable[12].mac,
                          command)

    def testfailswitchboot(self):
        command = ["update_interface", "--boot", "--interface=xge49",
                   "--switch=ut3gd1r01.aqd-unittest.ms.com"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out,
                         "cannot use the --autopg, --pg, or --boot options",
                         command)

    def testfailswitchip(self):
        command = ["update_interface", "--interface=xge49",
                   "--ip", self.net.tor_net[0].usable[1],
                   "--switch=ut3gd1r01.aqd-unittest.ms.com"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out, "use update_switch to update the IP", command)

    def testfailnointerface(self):
        command = ["update_interface", "--interface=xge49",
                   "--comments=This should fail",
                   "--switch=ut3gd1r01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Interface xge49 of ut3gd1r01.aqd-unittest.ms.com "
                         "not found",
                         command)

    def testupdateswitch(self):
        command = ["update_interface", "--interface=xge49",
                   "--comments=Some interface comments",
                   "--mac", self.net.tor_net[8].usable[0].mac,
                   "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifyupdateswitch(self):
        command = ["show_switch",
                   "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r06.aqd-unittest.ms.com", command)
        self.matchoutput(out,
                         "Interface: xge49 %s" %
                         self.net.tor_net[8].usable[0].mac,
                         command)
        self.matchoutput(out, "Comments: Some interface comments", command)


if __name__=='__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
