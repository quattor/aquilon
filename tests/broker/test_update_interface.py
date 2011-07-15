#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
        mac = self.net.unknown[0].usable[11].mac
        self.dsdb_expect_update("unittest02.one-nyp.ms.com", mac)
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--mac", mac])
        self.dsdb_verify()

    def testupdatebadmac(self):
        mac = self.net.tor_net[6].usable[0].mac
        command = ["update", "interface", "--interface", "eth0",
                   "--machine", "ut3c5n10", "--mac", mac]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "MAC address %s is already in use by on-board admin "
                         "interface xge49 of switch "
                         "ut3gd1r04.aqd-unittest.ms.com" % mac,
                         command)

    def testupdateut3c5n10eth0ip(self):
        oldip = self.net.unknown[0].usable[0]
        newip = self.net.unknown[0].usable[11]
        self.dsdb_expect_delete(oldip)
        self.dsdb_expect_add("unittest02.one-nyp.ms.com", newip, "eth0",
                             oldip.mac)
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--ip", newip])
        self.dsdb_verify()

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
        self.matchoutput(out, "Interface: eth0 %s boot=False" %
                         self.net.unknown[0].usable[11].mac.lower(), command)
        self.matchoutput(out, "Provides: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[11], command)
        self.matchoutput(out, "Interface: eth1 %s boot=True" %
                         self.net.unknown[0].usable[12].mac.lower(), command)
        self.matchoutput(out, "Provides: unknown [%s]" %
                         self.net.unknown[0].usable[12], command)
        # Verify that the primary name got updated
        self.matchoutput(out, "Primary Name: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[11], command)
        self.matchclean(out, str(self.net.unknown[0].usable[0]), command)

    def testverifycatut3c5n10interfaces(self):
        #FIX ME: this doesn't really test anything at the moment: needs to be
        #statefully parsing the interface output
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic" = nlist\(\s*'
                          r'"eth0", nlist\(\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.unknown[0].usable[11].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "%s"\s*\)\s*\);'
                          % self.net.unknown[0].usable[12].mac,
                          command)

    def testverifycatunittest02interfaces(self):
        net = self.net.unknown[0]
        eth0ip = net.usable[11]
        eth1ip = net.usable[12]
        # Use --generate as update_interface does not update the on-disk
        # templates
        command = "cat --hostname unittest02.one-nyp.ms.com --generate"
        out = self.commandtest(command.split(" "))
        # After flipping the boot flag, the static route should now appear on
        # eth0
        self.searchoutput(out,
                          r'"eth0", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"fqdn", "unittest02.one-nyp.ms.com",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "4.2.1.1",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (net.broadcast, net.gateway,
                           eth0ip, net.netmask),
                          command)
        # No "fqdn" here as "update interface --interface eth1 --boot" does not
        # transfer the primary IP. It is a question if it should...
        self.searchoutput(out,
                          r'"eth1", nlist\(\s*'
                          r'"bootproto", "static",\s*'
                          r'"broadcast", "%s",\s*'
                          r'"gateway", "%s",\s*'
                          r'"ip", "%s",\s*'
                          r'"netmask", "%s"\s*\)' %
                          (net.broadcast, net.gateway,
                           eth1ip, net.netmask),
                          command)
        self.searchoutput(out,
                          r'"eth1\.2", nlist\(\s*'
                          r'"bootproto", "none",\s*'
                          r'"physdev", "eth1",\s*'
                          r'"vlan", true\s*\)',
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
        mac = self.net.tor_net[8].usable[0].mac
        self.dsdb_expect_update("ut3gd1r06.aqd-unittest.ms.com", mac)
        command = ["update_interface", "--interface=xge49",
                   "--comments=Some interface comments",
                   "--mac", mac, "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyupdateswitch(self):
        command = ["show_switch",
                   "--switch=ut3gd1r06.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Switch: ut3gd1r06", command)
        self.matchoutput(out,
                         "Interface: xge49 %s" %
                         self.net.tor_net[8].usable[0].mac,
                         command)
        self.matchoutput(out, "Comments: Some interface comments", command)

    def testnotamachine(self):
        command = ["update", "interface", "--interface", "xge49",
                   "--machine", "ut3gd1r06.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a machine", command)

    def testnotaswitch(self):
        command = ["update", "interface", "--interface", "eth0",
                   "--switch", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a switch", command)

    def testfliproute1(self):
        command = ["update", "interface", "--interface", "eth0",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--nodefault_route"]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "Warning: machine unittest25.aqd-unittest.ms.com "
                         "has no default route, hope that's ok.", command)

    def testfliproute2(self):
        command = ["update", "interface", "--interface", "eth1",
                   "--machine", "unittest25.aqd-unittest.ms.com",
                   "--default_route"]
        self.noouttest(command)

    def testverifyfliproutecat(self):
        command = ["cat", "--hostname", "unittest25.aqd-unittest.ms.com",
                   "--generate"]
        out = self.commandtest(command)
        self.matchoutput(out, "'/system/network/default_gateway' = \"%s\";" %
                         self.net.unknown[1][2], command)


if __name__ == '__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
