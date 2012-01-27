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

    badhost = "unittest02.one-nyp.ms.com"

    def testupdateut3c5n10eth0macbad(self):
        # see testaddunittest02
        oldmac = self.net.unknown[0].usable[0].mac
        mac = self.net.unknown[0].usable[11].mac
        self.dsdb_expect_update(self.badhost, mac, fail=True)
        command = ["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--mac", mac,
                        "--comments", "Updated interface comments"]
        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "DSDB update failed", command)

        out = self.commandtest(["show", "host", "--hostname", self.badhost])
        self.matchoutput(out, "Interface: eth0 %s" % oldmac, command)

    def testupdateut3c5n10eth0macgood(self):
        mac = self.net.unknown[0].usable[11].mac
        self.dsdb_expect_update("unittest02.one-nyp.ms.com", mac)
        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--mac", mac,
                        "--comments", "Updated interface comments"])
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

    def testupdateut3c5n10eth0ipbad(self):
        oldip = self.net.unknown[0].usable[0]
        newip = self.net.unknown[0].usable[11]
        self.dsdb_expect_update_ip(self.badhost, "eth0", newip, fail=True)
        command = ["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--ip", newip]

        out = self.badrequesttest(command)
        self.dsdb_verify()
        self.matchoutput(out, "DSDB update failed", command)

        out = self.commandtest(["show", "host", "--hostname", self.badhost])
        self.matchoutput(out, "Primary Name: %s [%s]" % (self.badhost, oldip), command)

    def testupdateut3c5n10eth0ipgood(self):
        oldip = self.net.unknown[0].usable[0]
        newip = self.net.unknown[0].usable[11]
        self.dsdb_expect_update_ip(self.badhost, "eth0", newip)

        self.noouttest(["update", "interface", "--interface", "eth0",
                        "--machine", "ut3c5n10", "--ip", newip])
        self.dsdb_verify()

    def testfailaddip(self):
        command = ["update", "interface", "--interface", "eth1",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--mac", self.net.unknown[0].usable[12].mac,
                   "--ip", self.net.unknown[0].usable[12]]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Please use aq add_interface_address to add "
                         "a new IP address to the interface.",
                         command)

    def testupdateut3c5n10eth1(self):
        self.noouttest(["update", "interface", "--interface", "eth1",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--mac", self.net.unknown[0].usable[12].mac,
                        "--boot", "--model", "e1000"])

    def testupdateut3c5n10eth2(self):
        self.notfoundtest(["update", "interface", "--interface", "eth2",
            "--machine", "ut3c5n10", "--boot"])

    def testupdatebadhost(self):
        # Use host name instead of machine name
        self.notfoundtest(["update", "interface", "--interface", "eth0",
                           "--machine", "unittest02.one-nyp.ms.com"])

    def testupdatevlanmodel(self):
        command = ["update", "interface", "--machine", "ut3c5n10",
                   "--interface", "eth1.2", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model/vendor can not be set for a VLAN "
                         "interface", command)

    def testupdatebondingmodel(self):
        command = ["update", "interface", "--machine", "ut3c5n3",
                   "--interface", "bond0", "--model", "e1000"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Model/vendor can not be set for a bonding "
                         "interface", command)

    def testverifyupdateut3c5n10interfaces(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Comments: Updated interface comments", command)
        self.searchoutput(out, r"Interface: eth0 %s$" %
                          self.net.unknown[0].usable[11].mac.lower(), command)
        self.matchoutput(out, "Provides: unittest02.one-nyp.ms.com [%s]" %
                         self.net.unknown[0].usable[11], command)
        self.searchoutput(out, r"Interface: eth1 %s \[boot, default_route\]" %
                          self.net.unknown[0].usable[12].mac.lower(), command)
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
                          r'"eth0", create\("hardware/nic/generic/generic_nic",\s*'
                          r'"hwaddr", "%s"\s*\),'
                          % self.net.unknown[0].usable[11].mac,
                          command)
        self.searchoutput(out,
                          r'"eth1", create\("hardware/nic/intel/e1000",\s*'
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
                          r'"network_environment", "internal",\s*'
                          r'"network_type", "unknown",\s*'
                          r'"route", list\(\s*'
                          r'nlist\(\s*'
                          r'"address", "250.250.0.0",\s*'
                          r'"gateway", "4.2.1.1",\s*'
                          r'"netmask", "255.255.0.0"\s*\)\s*'
                          r'\)\s*\)' %
                          (net.broadcast, net.gateway,
                           eth0ip, net.netmask),
                          command)
        self.searchoutput(out, r'"eth1", nlist\(\s*"bootproto", "none"\s*\)',
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
        self.matchoutput(out, "cannot use the --boot option.", command)

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

    def testverifyfliprouteshow(self):
        command = ["show", "host", "--hostname", "unittest25.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Interface: eth0 %s [boot]" %
                         self.net.unknown[0].usable[20].mac, command)
        self.matchoutput(out, "Interface: eth1 %s [default_route]" %
                         self.net.unknown[0].usable[21].mac, command)

    def testbreakbond(self):
        command = ["update", "interface", "--machine", "ut3c5n3",
                   "--interface", "eth1", "--clear_master"]
        self.noouttest(command)
        # Should fail the second time
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth1 of machine "
                         "unittest21.aqd-unittest.ms.com is not a slave.",
                         command)


if __name__ == '__main__':
    import aquilon.aqdb.depends
    import nose

    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateInterface)
    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
