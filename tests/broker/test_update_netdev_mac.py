#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014  Contributor
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
"""Module for testing the poll network device command."""

import json
import re
import os
from collections import defaultdict
from time import sleep

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


# This suite replicates parts of test_poll_network_device testing update_network_device --discovered_macs.
# when aq_poll_network_device is removed, the remaining test methods should be moved
# here.
class TestUpdateNetworkDeviceMac(TestBrokerCommand):

    # Currently done by test_poll_network_device, can't run it twice
    # TODO when aq poll_network_device removed, these methods should be moved here
    # # test_prebind_server runs too late...
    # def testbindpollhelper(self):

    # # test_map_service runs too late...
    # def testmappollhelper(self):

    def getmacdata(self, switchfile):
        dir = os.path.dirname(os.path.realpath(__file__))
        out = open(os.path.join(dir, "..", "fakebin", "macdata.d", switchfile),
                   'r').read()
        return re.sub(r"\s+", " ", "".join(out))

    def testpollnp06bals03(self):
        command = ["update", "network_device", "--network_device", "np06bals03.ms.com",
                   "--discovered_macs", self.getmacdata("np06bals03")]
        self.noouttest(command)

    # Tests re-polling np06bals03 and polls np06fals01
    def testpollnp7(self):
        # Need to make sure that last_seen != creation_date for np06bals03
        # so sleep for 2 seconds here...
        sleep(2)
        # Issues deprecated warning.
        for sw in ["np06bals03", "np06fals01"]:
            command = ["update", "network_device", "--network_device", sw + ".ms.com",
                       "--discovered_macs", self.getmacdata(sw)]
            self.noouttest(command)

    def testrepollwithclear(self):
        # Forcing there to "normally" be a difference in last_seen and
        # creation_date to test that clear is working...
        sleep(2)
        # Issues deprecated warning.
        command = ["update", "network_device", "--network_device", "np06fals01.ms.com",
                   "--discovered_macs", self.getmacdata("np06fals01"), "--clear"]
        self.noouttest(command)

    # FIXME: Verify the poll and that last_seen != creation_date
    def testverifypollnp06bals03(self):
        command = "show network_device --network_device np06bals03.ms.com"
        out = self.commandtest(command.split(" "))
        r = re.compile(r'created:\s*(.*?),\s*last seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) == m.group(2),
                    "Expected creation date '%s' to be different from "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))

        colon_re = re.compile(r"([0-9a-f]{2})(?=.)")

        port_to_mac = defaultdict(list)
        for mac, port in json.loads(self.getmacdata("np06bals03")):
            # We have to add the separator colons
            port_to_mac[port].append(colon_re.sub(r"\1:", mac.lower()))

        for port, addrs in port_to_mac.items():
            pattern = r"Port: %s\n" % port
            pattern = pattern + "".join(r"\s+MAC: %s,.*\n" % mac
                                        for mac in sorted(addrs))
            self.searchoutput(out, pattern, command)

        for port in range(1, 50):
            if str(port) not in port_to_mac:
                self.searchclean(out, r"Port: %s\n" % port, command)

    def testverifypollnp06fals01(self):
        command = "show network_device --network_device np06fals01.ms.com"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out, r"Port: 49\s*MAC: 00:15:2c:1f:40:00,", command)
        r = re.compile(r'created:\s*(.*?),\s*last seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) != m.group(2),
                    "Expected creation date '%s' to be the same as "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))

    # Currently done by test_poll_network_device, update_network_device does not implement
    # --vlan yet.
    # TODO when aq poll_network_device removed, these methods should be moved here
    # def testpollut01ga2s01(self):

    # def testverifypollut01ga2s01(self):

    # def testverifyut11s01p1(self):

    # def testpollut01ga2s02(self):

    # def testverifypollut01ga2s02(self):

    # def testpollut01ga2s05(self):

    # def testpollnp01ga2s05(self):

    # def testpollbor(self):

    # These should be removed when aq poll_network_device is removed, we won't look for
    # tor switches in update_network_device
    # def testpolltype(self):

    # def testtypemismatch(self):

    def testbadtype(self):
        command = ["update", "network_device", "--network_device",
                   "ut3gd1r01.aqd-unittest.ms.com",
                   "--discovered_macs", self.getmacdata("ut3gd1r01.aqd-unittest.ms.com"),
                   "--type", "no-such-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown switch type 'no-such-type'.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateNetworkDeviceMac)
    unittest.TextTestRunner(verbosity=2).run(suite)
