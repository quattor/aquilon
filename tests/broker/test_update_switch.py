#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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
"""Module for testing the add switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestUpdateSwitch(TestBrokerCommand):

    def verifyswitch(self, switch, vendor, model,
                     rack, rackrow, rackcol,
                     serial=None, switch_type=None, ip=None, mac=None,
                     interface=None, comments=None):
        command = "show switch --switch %s" % switch
        out = self.commandtest(command.split(" "))
        (short, dot, dns_domain) = switch.partition(".")
        self.matchoutput(out, "Switch: %s" % short, command)
        if dns_domain:
            if ip:
                # Check both the primary name...
                self.matchoutput(out, "Primary Name: %s [%s]" % (switch, ip),
                                 command)
                # ... and the AddressAssignment record
                self.matchoutput(out, "Provides: %s [%s]" % (switch, ip),
                                 command)
            else:
                self.matchoutput(out, "Primary Name: %s" % switch, command)
        if switch_type is None:
            switch_type = 'tor'
        self.matchoutput(out, "Switch Type: %s" % switch_type, command)
        self.matchoutput(out, "Rack: %s" % rack, command)
        self.matchoutput(out, "Row: %s" % rackrow, command)
        self.matchoutput(out, "Column: %s" % rackcol, command)
        self.matchoutput(out, "Vendor: %s Model: %s" % (vendor, model),
                         command)
        if serial:
            self.matchoutput(out, "Serial: %s" % serial, command)
        else:
            self.matchclean(out, "Serial:", command)

        # Careful about indentation, do not mistake switch comments with
        # interface comments
        if comments:
            self.matchoutput(out, "\n  Comments: %s" % comments, command)
        else:
            self.matchclean(out, "\n  Comments:", command)

        if not interface:
            # FIXME: eventually this should be part of the model
            interface = "xge"
            self.matchoutput(out, "\n    Comments: Created automatically "
                             "by add_switch", command)
        if mac:
            self.searchoutput(out, r"Interface: %s %s$" %
                             (interface, mac), command)
        else:
            self.searchoutput(out, r"Interface: %s \(no MAC addr\)$" %
                             interface, command)
#        for port in range(1,49):
#            self.matchoutput(out, "Switch Port %d" % port, command)
        return (out, command)

    def testfailnomodel(self):
        command = ["update", "switch", "--vendor", "generic",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model uttorswitch, vendor generic, "
                         "machine_type switch not found.",
                         command)

    # FIXME: "without interface" is no longer true
    def testupdatewithoutinterface(self):
        newip = self.net.tor_net[6].usable[1]
        self.dsdb_expect_update_ip("ut3gd1r04.aqd-unittest.ms.com", "xge49", newip)
        command = ["update", "switch", "--type", "bor",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com",
                   "--ip", newip, "--model", "uttorswitch",
                   "--comments", "Some new switch comments"]
        self.noouttest(command)
        self.dsdb_verify()

    def testupdatemisc(self):
        command = ["update", "switch",
                   "--switch", "ut3gd1r05.aqd-unittest.ms.com",
                   "--rack", "ut4", "--model", "uttorswitch",
                   "--vendor", "hp", "--serial", "SNgd1r05_new"]
        self.noouttest(command)

    def testaddinterface(self):
        ip = self.net.tor_net[8].usable[0]
        mac = self.net.tor_net[8].usable[1].mac
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add("ut3gd1r06.aqd-unittest.ms.com", ip, "xge49", mac)
        command = ["add_interface", "--switch=ut3gd1r06.aqd-unittest.ms.com",
                   "--interface=xge49", "--mac", mac]
        self.noouttest(command)
        (out, cmd) = self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com",
                                       "generic", "temp_switch", "ut3", "a", "3",
                                       switch_type='tor',
                                       ip=ip, mac=mac, interface="xge49")
        # Verify that the auto-created dummy interface is gone
        self.matchclean(out, "Interface: xge ", command)
        self.dsdb_verify()

    def testupdatewithinterface(self):
        newip = self.net.tor_net[8].usable[1]
        self.dsdb_expect_update_ip("ut3gd1r06.aqd-unittest.ms.com", "xge49", newip)
        command = ["update", "switch",
                   "--switch", "ut3gd1r06.aqd-unittest.ms.com",
                   "--ip", newip]
        self.noouttest(command)
        self.dsdb_verify()


    def testverifyupdatewithoutinterface(self):
        self.verifyswitch("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[6].usable[1],
                          mac=self.net.tor_net[6].usable[0].mac,
                          interface="xge49",
                          comments="Some new switch comments")

    def testverifyupdatemisc(self):
        self.verifyswitch("ut3gd1r05.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut4", "a", "4", "SNgd1r05_new", switch_type='tor',
                          ip=self.net.tor_net[7].usable[0], interface="xge49")

    def testverifyupdatewithinterface(self):
        self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[8].usable[1],
                          mac=self.net.tor_net[8].usable[1].mac,
                          interface="xge49")

    def testverifydsdbrollback(self):
        self.verifyswitch("ut3gd1r07.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[9].usable[0])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
