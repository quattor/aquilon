#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2013  Contributor
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
"""Module for testing the map_dns_domain command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestMapDnsDomain(TestBrokerCommand):

    def test_100_map_ut(self):
        cmd = "map dns domain --room utroom1 --dns_domain aqd-unittest.ms.com"
        self.noouttest(cmd.split(" "))

    def test_105_map_ny(self):
        cmd = "map dns domain --campus ny --dns_domain new-york.ms.com"
        self.noouttest(cmd.split(" "))

    def test_110_map_ut3(self):
        # This is used to test that machines in this rack do not have
        # aqd-unittest.ms.com listed twice in sysloc/dns_search_domains
        cmd = "map dns domain --rack ut3 --dns_domain aqd-unittest.ms.com"
        self.noouttest(cmd.split(" "))

    def test_200_verify_aqd_unittest(self):
        cmd = "show dns_domain --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Mapped to: Room utroom1", cmd)
        self.matchoutput(out, "Mapped to: Rack ut3", cmd)
        self.matchclean(out, "Campus", cmd)

    def test_205_verify_new_york(self):
        cmd = "show dns_domain --dns_domain new-york.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Mapped to: Campus ny", cmd)
        self.matchclean(out, "Room", cmd)
        self.matchclean(out, "Rack", cmd)

    def test_300_search_dns_map(self):
        cmd = "search dns domain map --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out,
                         "DNS Domain: aqd-unittest.ms.com Map: Room utroom1",
                         cmd)
        self.matchoutput(out,
                         "DNS Domain: aqd-unittest.ms.com Map: Rack ut3",
                         cmd)

    def test_305_search_location(self):
        command = ["search", "dns", "domain", "map", "--room", "utroom1",
                   "--include_parents"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "DNS Domain: aqd-unittest.ms.com Map: Room utroom1",
                         command)
        self.matchoutput(out,
                         "DNS Domain: new-york.ms.com Map: Campus ny",
                         command)

    def test_305_search_location_exact(self):
        command = ["search", "dns", "domain", "map", "--room", "utroom1"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "DNS Domain: aqd-unittest.ms.com Map: Room utroom1",
                         command)
        self.matchclean(out, "new-york.ms.com", command)

    def test_400_map_td1_first(self):
        command = ["map", "dns", "domain", "--room", "utroom1",
                   "--dns_domain", "td1.aqd-unittest.ms.com", "--position", 0]
        self.noouttest(command)

    def test_410_map_td2_middle(self):
        command = ["map", "dns", "domain", "--room", "utroom1",
                   "--dns_domain", "td2.aqd-unittest.ms.com", "--position", 1]
        self.noouttest(command)

    def test_450_verify_positions(self):
        command = ["search", "dns", "domain", "map", "--room", "utroom1"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r"DNS Domain: td1.aqd-unittest.ms.com Map: Room utroom1\s*"
                          r"Position: 0\s*"
                          r"DNS Domain: td2.aqd-unittest.ms.com Map: Room utroom1\s*"
                          r"Position: 1\s*"
                          r"DNS Domain: aqd-unittest.ms.com Map: Room utroom1\s*"
                          r"Position: 2\s*",
                          command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapDnsDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
