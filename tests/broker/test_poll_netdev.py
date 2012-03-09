#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
import os
import re
import socket
from collections import defaultdict
from time import sleep

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestPollNetworkDevice(TestBrokerCommand):
    def getmacdata(self, switchfile):
        dir = os.path.dirname(os.path.realpath(__file__))
        out = open(os.path.join(dir, "..", "fakebin", "macdata.d", switchfile),
                   'r').read()
        return re.sub(r"\s+", " ", "".join(out))

    # test_prebind_server runs too late...
    def testbindpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["bind", "server", "--service", service,
                        "--instance", "unittest",
                        "--hostname", "nyaqd1.ms.com"])

    # test_map_service runs too late...
    def testmappollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["map", "service", "--service", service,
                        "--instance", "unittest", "--building", "ut"])

    def testpollnp06bals03(self):
        command = ["poll", "network_device", "--network_device", "np06bals03.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "No jump host for np06bals03.ms.com, running "
                         "discovery from %s." % socket.gethostname(), command)

    # Tests re-polling np06bals03 and polls np06fals01
    def testpollnp7(self):
        # Need to make sure that last_seen != creation_date for np06bals03
        # so sleep for 2 seconds here...
        sleep(2)
        # Issues deprecated warning.
        self.successtest(["poll", "network_device", "--rack", "np7", "--type", "tor"])

    def testrepollwithclear(self):
        # Forcing there to "normally" be a difference in last_seen and
        # creation_date to test that clear is working...
        sleep(2)
        # Issues deprecated warning.
        self.successtest(["poll_network_device", "--network_device=np06fals01.ms.com",
                          "--clear"])

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
        self.searchoutput(out, r"Port: 49$\s+MAC: 00:15:2c:1f:40:00", command)
        r = re.compile(r'created:\s*(.*?),\s*last seen:\s*(.*?)\s*$', re.M)
        m = self.searchoutput(out, r, command)
        self.failIf(m.group(1) != m.group(2),
                    "Expected creation date '%s' to be the same as "
                    "last seen '%s' in output:\n%s" %
                    (m.group(1), m.group(2), out))

    def testpollut01ga2s01(self):
        # Issues deprecated warning.
        command = ["poll", "network_device", "--vlan", "--network_device",
                   "ut01ga2s01.aqd-unittest.ms.com"]
        err = self.statustest(command)
        net = self.net["vmotion_net"]
        self.matchoutput(err,
                         "Switch ut01ga2s01.aqd-unittest.ms.com: skipping VLAN "
                         "714, because network bitmask value 24 differs from "
                         "prefixlen 26 of network %s." % net.name,
                         command)
        service = self.config.get("broker", "poll_helper_service")
        self.matchoutput(err,
                         "Using jump host nyaqd1.ms.com from service instance "
                         "%s/unittest to run discovery "
                         "for switch ut01ga2s01.aqd-unittest.ms.com." %
                         (service),
                         command)

    def testverifypollut01ga2s01(self):
        command = "show network_device --network_device ut01ga2s01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        for i in range(1, 13):
            self.searchoutput(out,
                              r"Port: %d\s+MAC: %s" %
                              (i, self.net["vmotion_net"].usable[i + 1].mac),
                              command)
        self.matchoutput(out, "VLAN 701: %s" % self.net["vm_storage_net"].ip,
                         command)
        # I was lazy... really this should be some separate non-routeable
        # subnet and not the tor_net2...
        self.matchoutput(out, "VLAN 702: %s" % self.net["vmotion_net"].ip,
                         command)
        self.matchoutput(out, "VLAN 710: %s" % self.net["ut01ga2s01_v710"].ip, command)
        self.matchoutput(out, "VLAN 711: %s" % self.net["ut01ga2s01_v711"].ip, command)
        self.matchoutput(out, "VLAN 712: %s" % self.net["ut01ga2s01_v712"].ip, command)
        self.matchoutput(out, "VLAN 713: %s" % self.net["ut01ga2s01_v713"].ip, command)
        self.matchclean(out, "VLAN 714", command)

    def testverifyut11s01p1(self):
        command = "show machine --machine ut11s01p1"
        out = self.commandtest(command.split())
        self.matchoutput(out,
                         "Last switch poll: "
                         "ut01ga2s01.aqd-unittest.ms.com port 1 [",
                         command)

    def testpollut01ga2s02(self):
        self.successtest(["poll", "network_device", "--vlan",
                          "--network_device", "ut01ga2s02.aqd-unittest.ms.com"])

    def testverifypollut01ga2s02(self):
        command = "show network_device --network_device ut01ga2s02.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        for i in range(13, 25):
            self.searchoutput(out,
                              r"Port: %d\s+MAC: %s" %
                              (i - 12, self.net["vmotion_net"].usable[i + 1].mac),
                             command)
        self.matchoutput(out, "VLAN 701: %s" % self.net["vm_storage_net"].ip,
                         command)
        # I was lazy... really this should be some separate non-routeable
        # subnet and not the tor_net2...
        self.matchoutput(out, "VLAN 702: %s" % self.net["vmotion_net"].ip,
                         command)
        self.matchoutput(out, "VLAN 710: %s" % self.net["ut01ga2s02_v710"].ip, command)
        self.matchoutput(out, "VLAN 711: %s" % self.net["ut01ga2s02_v711"].ip, command)
        self.matchoutput(out, "VLAN 712: %s" % self.net["ut01ga2s02_v712"].ip, command)
        self.matchoutput(out, "VLAN 713: %s" % self.net["ut01ga2s02_v713"].ip, command)

    def testpollut01ga2s03(self):
        self.successtest(["poll", "network_device", "--vlan",
                          "--network_device", "ut01ga2s03.aqd-unittest.ms.com"])

    def testpollut01ga2s04(self):
        self.successtest(["poll", "network_device", "--vlan",
                          "--network_device", "ut01ga2s04.aqd-unittest.ms.com"])

    def testpollut01ga2s05(self):
        self.successtest(["poll", "network_device",
                          "--network_device", "ut01ga2s05.aqd-unittest.ms.com"])

    def testpollnp01ga2s05(self):
        self.successtest(["poll", "network_device",
                          "--network_device", "np01ga2s05.one-nyp.ms.com"])

    def testpollbor(self):
        command = ["poll", "network_device", "--vlan",
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Skipping VLAN probing on switch "
                         "ut3gd1r01.aqd-unittest.ms.com, it's "
                         "not a ToR network device.",
                         command)

    def testpolltype(self):
        # We make use of poll_switch reporting the (lack of the) jump host for
        # every switch it touches
        command = ["poll", "network_device", "--rack", "ut3", "--type", "bor"]
        err = self.statustest(command)
        self.matchoutput(err, "ut3gd1r01.aqd-unittest.ms.com", command)
        # update_switch changes the type of ut3gd1r04 to 'bor'
        self.matchoutput(err, "ut3gd1r04.aqd-unittest.ms.com", command)
        self.matchoutput(err, "ut3gd1r07.aqd-unittest.ms.com", command)
        self.matchclean(err, "ut3gd1r05.aqd-unittest.ms.com", command)
        self.matchclean(err, "ut3gd1r06.aqd-unittest.ms.com", command)

    def testtypemismatch(self):
        command = ["poll", "network_device", "--type", "tor",
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Switch ut3gd1r01.aqd-unittest.ms.com is not "
                         "a tor switch.",
                         command)

    def testbadtype(self):
        command = ["poll", "network_device", "--type", "no-such-type",
                   "--network_device", "ut3gd1r01.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown switch type 'no-such-type'.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPollNetworkDevice)
    unittest.TextTestRunner(verbosity=2).run(suite)
