#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2016  Contributor
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
"""Module for testing the search service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestSearchService(TestBrokerCommand):

    def test_100_search_by_server(self):
        command = ["search_service", "--server_hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "utsvc/utsi2", command)
        self.matchclean(out, "utsvc/utsi1", command)
        self.matchclean(out, "afs", command)

    def test_110_search_by_client(self):
        command = ["search_service", "--client_hostname", "unittest00.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "afs/q.ny.ms.com", command)
        self.matchoutput(out, "bootserver/unittest", command)
        self.matchoutput(out, "dns/unittest", command)
        self.matchoutput(out, "ntp/pa.ny.na", command)
        self.matchoutput(out, "support-group/ec-service", command)
        self.matchclean(out, "bootserver/one-nyp", command)
        self.matchclean(out, "dns/one-nyp", command)

    def test_120_has_clients(self):
        command = ["search_service", "--has_clients"]
        out = self.commandtest(command)
        self.matchoutput(out, "afs/afs-by-net", command)
        self.matchoutput(out, "afs/q.ny.ms.com", command)
        self.matchoutput(out, "aqd/ny-prod", command)
        self.matchoutput(out, "bootserver/one-nyp", command)
        self.matchoutput(out, "bootserver/unittest", command)
        self.matchoutput(out, "dns/one-nyp", command)
        self.matchoutput(out, "dns/unittest", command)
        self.matchoutput(out, "esx_management_server/ut.a", command)
        self.matchoutput(out, "esx_management_server/ut.b", command)
        self.matchoutput(out, "ntp/pa.ny.na", command)
        self.matchoutput(out, "support-group/ec-service", command)
        self.matchoutput(out, "syslogng/ny-prod", command)
        self.matchoutput(out, "utsvc/utsi1", command)
        self.matchoutput(out, "utsvc/utsi2", command)
        self.matchoutput(out, "vmseasoning/pepper", command)
        self.matchoutput(out, "vmseasoning/salt", command)
        self.matchclean(out, "afs/q.ln.ms.com", command)
        self.matchclean(out, "scope_test/target-personality", command)
        self.matchclean(out, "scope_test/scope-building", command)
        self.matchclean(out, "poll_helper/unittest", command)
        self.matchclean(out, "unmapped/instance1", command)
        self.matchclean(out, "utnotify/localhost", command)
        self.matchclean(out, "vcenter/ut", command)

    def test_130_no_clients(self):
        command = ["search_service", "--no_clients"]
        out = self.commandtest(command)
        self.matchoutput(out, "afs/q.ln.ms.com", command)
        self.matchoutput(out, "camelcase/camelcase", command)
        self.matchoutput(out, "scope_test/target-personality", command)
        self.matchoutput(out, "scope_test/scope-building", command)
        self.matchoutput(out, "poll_helper/unittest", command)
        self.matchoutput(out, "unmapped/instance1", command)
        self.matchoutput(out, "utnotify/localhost", command)
        self.matchoutput(out, "vcenter/ut", command)
        self.matchclean(out, "afs/ny-prod", command)
        self.matchclean(out, "bootserver/one-nyp", command)
        self.matchclean(out, "bootserver/unittest", command)

    def test_140_server_location(self):
        command = ["search_service", "--server_building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "bootserver/unittest", command)
        self.matchoutput(out, "chooser1/ut.a", command)
        self.matchoutput(out, "chooser1/ut.b", command)
        self.matchoutput(out, "chooser1/ut.c", command)
        self.matchoutput(out, "chooser2/ut.a", command)
        self.matchoutput(out, "chooser2/ut.c", command)
        self.matchoutput(out, "chooser3/ut.a", command)
        self.matchoutput(out, "chooser3/ut.b", command)
        self.matchoutput(out, "dns/unittest", command)
        self.matchoutput(out, "utnotify/localhost", command)
        self.matchoutput(out, "utsvc/utsi1", command)
        self.matchoutput(out, "utsvc/utsi2", command)
        self.matchclean(out, "bootserver/one-nyp", command)
        self.matchclean(out, "dns/one-nyp", command)

    def test_150_client_location(self):
        command = ["search_service", "--client_building", "np"]
        out = self.commandtest(command)
        self.matchoutput(out, "afs/q.ny.ms.com", command)
        self.matchoutput(out, "aqd/ny-prod", command)
        self.matchoutput(out, "bootserver/one-nyp", command)
        self.matchoutput(out, "dns/one-nyp", command)
        self.matchoutput(out, "ntp/pa.ny.na", command)
        self.matchoutput(out, "support-group/ec-service", command)
        self.matchoutput(out, "syslogng/ny-prod", command)
        self.matchoutput(out, "utsvc/utsi1", command)
        self.matchclean(out, "bootserver/unittest", command)
        self.matchclean(out, "dns/unittest", command)
        self.matchclean(out, "utsvc/utsi2", command)
        self.matchclean(out, "vmseasoning", command)
        self.matchclean(out, "esx_management_server", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchService)
    unittest.TextTestRunner(verbosity=2).run(suite)
