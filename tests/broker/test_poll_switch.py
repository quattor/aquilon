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
"""Module for testing the poll tor_switch command."""

import re
import unittest
from time import sleep

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPollSwitch(TestBrokerCommand):

    def testpollnp06bals03(self):
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch",
                          "--tor_switch", "np06bals03.ms.com"])

    # Tests re-polling np06bals03 and polls np06fals01
    def testpollnp7(self):
        # Need to make sure that last_seen != creation_date for np06bals03
        # so sleep for 2 seconds here...
        sleep(2)
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch", "--rack", "np7"])

    def testrepollwithclear(self):
        # Forcing there to "normally" be a difference in last_seen and
        # creation_date to test that clear is working...
        sleep(2)
        # Issues deprecated warning.
        self.successtest(["poll_tor_switch", "--tor_switch=np06fals01.ms.com",
                          "--clear"])

    # FIXME: Verify the poll and that last_seen != creation_date
    def testverifypollnp06bals03(self):
        command = "show tor_switch --tor_switch np06bals03.ms.com"
        out = self.commandtest(command.split(" "))
        r = re.compile(r'^\s*Created:\s*(.*?)\s*Last Seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) == m.group(2),
                    "Expected creation date '%s' to be different from "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))
        self.matchoutput(out, "Port 17: 00:30:48:66:3a:62", command)
        self.matchoutput(out, "Port 2: 00:1f:29:c4:39:ba", command)
        self.matchoutput(out, "Port 22: 00:30:48:66:38:e6", command)
        self.matchoutput(out, "Port 4: 00:1f:29:c4:29:ca", command)
        self.matchoutput(out, "Port 5: 00:1f:29:68:53:ca", command)
        self.matchoutput(out, "Port 27: 00:30:48:66:3a:28", command)
        self.matchoutput(out, "Port 20: 00:30:48:66:38:da", command)
        self.matchoutput(out, "Port 39: 00:30:48:98:4d:a3", command)
        self.matchoutput(out, "Port 24: 00:30:48:66:3a:2a", command)
        self.matchoutput(out, "Port 14: 00:1f:29:c4:39:12", command)
        self.matchoutput(out, "Port 3: 00:1f:29:c4:09:ee", command)
        self.matchoutput(out, "Port 49: 00:1a:6c:9e:e3:1e", command)
        self.matchoutput(out, "Port 21: 00:30:48:66:3a:2e", command)
        self.matchoutput(out, "Port 11: 00:1f:29:68:93:e0", command)
        self.matchoutput(out, "Port 31: 00:30:48:98:4d:0a", command)
        self.matchoutput(out, "Port 7: 00:1f:29:c4:19:d0", command)
        self.matchoutput(out, "Port 8: 00:1f:29:c4:59:b0", command)
        self.matchoutput(out, "Port 12: 00:1f:29:c4:19:f2", command)
        self.matchoutput(out, "Port 50: 00:1d:71:73:55:40", command)
        self.matchoutput(out, "Port 40: 00:30:48:98:4d:cc", command)
        self.matchoutput(out, "Port 34: 00:30:48:98:4d:83", command)
        self.matchoutput(out, "Port 50: 00:1a:6c:9e:de:8e", command)
        self.matchoutput(out, "Port 29: 00:30:48:98:4d:5b", command)
        self.matchoutput(out, "Port 10: 00:1f:29:c4:39:14", command)
        self.matchoutput(out, "Port 37: 00:30:48:98:4d:96", command)
        self.matchoutput(out, "Port 49: 00:1d:71:73:53:80", command)
        self.matchoutput(out, "Port 33: 00:30:48:98:4d:97", command)
        self.matchoutput(out, "Port 36: 00:30:48:98:4d:98", command)
        self.matchoutput(out, "Port 49: 00:00:0c:07:ac:01", command)
        self.matchoutput(out, "Port 9: 00:1f:29:c4:29:6a", command)
        self.matchoutput(out, "Port 35: 00:30:48:98:4d:8a", command)
        self.matchoutput(out, "Port 50: 00:00:0c:07:ac:02", command)
        self.matchoutput(out, "Port 32: 00:30:48:98:4d:8b", command)
        self.matchoutput(out, "Port 28: 00:30:48:66:3a:22", command)
        self.matchoutput(out, "Port 18: 00:30:48:66:3a:36", command)
        self.matchoutput(out, "Port 19: 00:30:48:66:3a:46", command)
        self.matchoutput(out, "Port 16: 00:1f:29:68:83:4c", command)
        self.matchoutput(out, "Port 25: 00:30:48:66:3a:38", command)
        self.matchoutput(out, "Port 15: 00:1f:29:c4:59:fe", command)
        self.matchoutput(out, "Port 30: 00:30:48:98:4d:c6", command)
        self.matchoutput(out, "Port 6: 00:1f:29:68:63:ec", command)
        self.matchoutput(out, "Port 23: 00:30:48:66:3a:60", command)

    def testverifypollnp06fals01(self):
        command = "show tor_switch --tor_switch np06fals01.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Port 49: 00:15:2c:1f:40:00", command)
        r = re.compile(r'^\s*Created:\s*(.*?)\s*Last Seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) != m.group(2),
                    "Expected creation date '%s' to be the same as "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))

    def testpollut01ga2s01(self):
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch", "--vlan",
                          "--tor_switch", "ut01ga2s01.aqd-unittest.ms.com"])

    def testverifypollut01ga2s01(self):
        command = "show tor_switch --tor_switch ut01ga2s01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        for i in range(1, 13):
            self.matchoutput(out,
                             "Port %d: %s" %
                             (i, self.net.tor_net2[2].usable[i + 1].mac),
                         command)
        self.matchoutput(out, "VLAN 701: %s" % self.net.vm_storage_net[0].ip,
                         command)
        # I was lazy... really this should be some separate non-routeable
        # subnet and not the tor_net2...
        self.matchoutput(out, "VLAN 702: %s" % self.net.tor_net2[2].ip,
                         command)
        self.matchoutput(out, "VLAN 710: %s" % self.net.unknown[2].ip, command)
        self.matchoutput(out, "VLAN 711: %s" % self.net.unknown[3].ip, command)
        self.matchoutput(out, "VLAN 712: %s" % self.net.unknown[4].ip, command)
        self.matchoutput(out, "VLAN 713: %s" % self.net.unknown[5].ip, command)

    def testpollut01ga2s02(self):
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch", "--vlan",
                          "--tor_switch", "ut01ga2s02.aqd-unittest.ms.com"])

    def testverifypollut01ga2s02(self):
        command = "show tor_switch --tor_switch ut01ga2s02.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        for i in range(13, 25):
            self.matchoutput(out,
                             "Port %d: %s" %
                             (i - 12, self.net.tor_net2[2].usable[i + 1].mac),
                             command)
        self.matchoutput(out, "VLAN 701: %s" % self.net.vm_storage_net[0].ip,
                         command)
        # I was lazy... really this should be some separate non-routeable
        # subnet and not the tor_net2...
        self.matchoutput(out, "VLAN 702: %s" % self.net.tor_net2[2].ip,
                         command)
        self.matchoutput(out, "VLAN 710: %s" % self.net.unknown[6].ip, command)
        self.matchoutput(out, "VLAN 711: %s" % self.net.unknown[7].ip, command)
        self.matchoutput(out, "VLAN 712: %s" % self.net.unknown[8].ip, command)
        self.matchoutput(out, "VLAN 713: %s" % self.net.unknown[9].ip, command)

    def testpollut01ga2s03(self):
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch",
                          "--tor_switch", "ut01ga2s03.aqd-unittest.ms.com"])

    def testpollnp01ga2s03(self):
        # Issues deprecated warning.
        self.successtest(["poll", "tor_switch",
                          "--tor_switch", "np01ga2s03.one-nyp.ms.com"])

    def testpollbor(self):
        command = ["poll", "switch", "--vlan",
                   "--switch", "ut3gd1r01.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Skipping VLAN probing on switch "
                         "ut3gd1r01.aqd-unittest.ms.com, it's not a ToR switch.",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPollSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)
