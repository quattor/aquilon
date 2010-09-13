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
"""Module for testing the add switch command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

class TestUpdateSwitch(TestBrokerCommand):

    def testfailnomodel(self):
        command = ["update", "switch", "--vendor", "generic",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Model uttorswitch, vendor generic, "
                         "machine_type switch not found.",
                         command)

    def testupdatewithoutinterface(self):
        oldip = self.net.tor_net[6].usable[0]
        newip = self.net.tor_net[6].usable[1]
        self.dsdb_expect_delete(oldip)
        self.dsdb_expect_add("ut3gd1r04.aqd-unittest.ms.com", newip)
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
        command = ["add_interface", "--switch=ut3gd1r06.aqd-unittest.ms.com",
                   "--interface=xge49",
                   "--mac", self.net.tor_net[8].usable[1].mac]
        self.noouttest(command)

    def testupdatewithinterface(self):
        oldip = self.net.tor_net[8].usable[0]
        newip = self.net.tor_net[8].usable[1]
        self.dsdb_expect_delete(oldip)
        self.dsdb_expect_add("ut3gd1r06.aqd-unittest.ms.com", newip)
        command = ["update", "switch",
                   "--switch", "ut3gd1r06.aqd-unittest.ms.com",
                   "--ip", newip]
        self.noouttest(command)
        self.dsdb_verify()

    def verifyswitch(self, switch, vendor, model,
                     rack, rackrow, rackcol,
                     serial=None, switch_type=None, ip=None, comments=None):
        command = "show switch --switch %s" % switch
        out = self.commandtest(command.split(" "))
        (short, dot, dns_domain) = switch.partition(".")
        self.matchoutput(out, "Switch: %s" % short, command)
        if dns_domain:
            if ip:
                self.matchoutput(out, "Primary Name: %s [%s]" %
                                 (switch, ip), command)
            else:
                self.matchoutput(out, "Primary Name: %s" % switch,
                                 command)
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
        if comments:
            self.matchoutput(out, "Comments: %s" % comments, command)
        else:
            self.matchclean(out, "Comments:", command)
#        for port in range(1,49):
#            self.matchoutput(out, "Switch Port %d" % port, command)
        return (out, command)

    def testverifyupdatewithoutinterface(self):
        self.verifyswitch("ut3gd1r04.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut3", "a", "3", switch_type='bor',
                          ip=self.net.tor_net[6].usable[1],
                          comments="Some new switch comments")

    def testverifyupdatemisc(self):
        self.verifyswitch("ut3gd1r05.aqd-unittest.ms.com", "hp", "uttorswitch",
                          "ut4", "a", "4", "SNgd1r05_new", switch_type='tor',
                          ip=self.net.tor_net[7].usable[0])

    def testverifyupdatewithinterface(self):
        self.verifyswitch("ut3gd1r06.aqd-unittest.ms.com", "generic",
                          "temp_switch", "ut3", "a", "3", switch_type='tor',
                          ip=self.net.tor_net[8].usable[1])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
