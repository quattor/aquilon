#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the unmap_dns_domain command."""

if __name__ == '__main__':
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUnmapDnsDomain(TestBrokerCommand):

    def test_100_unmap_dns_domain(self):
        cmd = "unmap dns domain --room utroom1 --dns_domain aqd-unittest.ms.com"
        self.noouttest(cmd.split(" "))

    def test_200_verify_unmap_dns_domain(self):
        cmd = "show dns_domain --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "DNS Domain: aqd-unittest.ms.com", cmd)
        self.matchclean(out, "Room", cmd)

    def test_210_verify_show_map(self):
        cmd = "search dns domain map --dns_domain aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Rack ut3", cmd)
        self.matchclean(out, "Room", cmd)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnmapDnsDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
