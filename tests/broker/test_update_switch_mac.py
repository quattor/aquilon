#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""Module for testing the poll switch command."""

import re
import os
import unittest
from time import sleep
import socket

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

# This suite replicates parts of test_poll_switch testing update_switch --discovered_macs.
# when aq_poll_switch is removed, the remaining test methods should be moved
# here.
class TestUpdateSwitchMac(TestBrokerCommand):

    # Currently done by test_poll_switch, can't run it twice
    # TODO when aq poll_switch removed, these methods should be moved here
    # # test_prebind_server runs too late...
    # def testbindpollhelper(self):

    # # test_map_service runs too late...
    # def testmappollhelper(self):

    def getmacdata(self, switchfile):
        dir = os.path.dirname(os.path.realpath(__file__))
        out = open(os.path.join(dir, "..", "fakebin", "macdata.d",
                               switchfile), 'r').read()
        return re.sub("\s+", " ", "".join(out))

    def testpollnp06bals03(self):
        command = ["update", "switch", "--switch", "np06bals03.ms.com",
                   "--discovered_macs", self.getmacdata("np06bals03")]
        self.noouttest(command)

    # Tests re-polling np06bals03 and polls np06fals01
    def testpollnp7(self):
        # Need to make sure that last_seen != creation_date for np06bals03
        # so sleep for 2 seconds here...
        sleep(2)
        # Issues deprecated warning.
        for sw in ["np06bals03", "np06fals01"]:
            command = ["update", "switch", "--switch", sw + ".ms.com",
                       "--discovered_macs", self.getmacdata(sw)]
            self.noouttest(command)

    def testrepollwithclear(self):
        # Forcing there to "normally" be a difference in last_seen and
        # creation_date to test that clear is working...
        sleep(2)
        # Issues deprecated warning.
        command = ["update", "switch", "--switch", "np06fals01.ms.com",
                   "--discovered_macs", self.getmacdata("np06fals01"), "--clear"]
        self.noouttest(command)

    # FIXME: Verify the poll and that last_seen != creation_date
    def testverifypollnp06bals03(self):
        command = "show switch --switch np06bals03.ms.com"
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
        command = "show switch --switch np06fals01.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Port 49: 00:15:2c:1f:40:00", command)
        r = re.compile(r'^\s*Created:\s*(.*?)\s*Last Seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) != m.group(2),
                    "Expected creation date '%s' to be the same as "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))

    # Currently done by test_poll_switch, update_switch does not implement
    # --vlan yet.
    # TODO when aq poll_switch removed, these methods should be moved here
    # def testpollut01ga2s01(self):

    # def testverifypollut01ga2s01(self):

    # def testverifyut11s01p1(self):

    # def testpollut01ga2s02(self):

    # def testverifypollut01ga2s02(self):

    # def testpollut01ga2s03(self):

    # def testpollnp01ga2s03(self):

    # def testpollbor(self):

    # These should be removed when aq poll_switch is removed, we won't look for
    # tor switches in update_switch
    # def testpolltype(self):

    # def testtypemismatch(self):

    def testbadtype(self):
        command = ["update", "switch", "--switch",
                   "ut3gd1r01.aqd-unittest.ms.com", 
                   "--discovered_macs", self.getmacdata("ut3gd1r01.aqd-unittest.ms.com"),
                   "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown switch type 'no-such-type'.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateSwitchMac)
    unittest.TextTestRunner(verbosity=2).run(suite)
