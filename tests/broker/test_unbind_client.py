#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the unbind client command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestUnbindClient(TestBrokerCommand):
    def test_100_bind_unmapped(self):
        command = ["bind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance unmapped/instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_105_verify_bind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unmapped", command)

    def test_110_bind_unmapped_unbuilt(self):
        command = ["bind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "aquilon94.aqd-unittest.ms.com adding binding for "
                         "service instance unmapped/instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_115_verify_bind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "not found", command)

    def test_120_unbind_unmapped(self):
        command = ["unbind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_125_verify_unbind_search(self):
        command = ["search_host", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_125_verify_unbind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "unmapped", command)

    def test_130_unbind_unmapped_unbuilt(self):
        command = ["unbind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Warning: Host aquilon94.aqd-unittest.ms.com is "
                         "missing the following required services, please run "
                         "'aq reconfigure': afs, aqd, bootserver, dns, lemon, "
                         "ntp, support-group, syslogng.",
                         command)

    def test_135_verify_unbind_search_unbuilt(self):
        command = ["search_host", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_135_verify_unbind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "not found", command)

    def test_200_bad_service(self):
        command = ["unbind_client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "no-such-service"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service no-such-service not found.", command)

    def test_200_bad_host(self):
        command = ["unbind_client", "--hostname", "badhost.aqd-unittest.ms.com",
                   "--service", "afs"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Host badhost.aqd-unittest.ms.com not found.",
                         command)

    def test_200_reject_unbind_required_arch(self):
        command = "unbind client --hostname unittest02.one-nyp.ms.com --service afs"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Service afs is required for archetype aquilon, the "
                         "binding cannot be removed.",
                         command)

    def test_200_reject_unbind_required_pers(self):
        command = ["unbind_client", "--hostname", "aquilon81.aqd-unittest.ms.com",
                   "--service", "chooser1"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Service chooser1 is required for personality "
                         "aquilon/unixeng-test@current, the binding cannot be removed.",
                         command)

    def test_200_reject_unbind_not_bound(self):
        command = ["unbind_client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "esx_management_server"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service esx_management_server is not bound to "
                         "host unittest02.one-nyp.ms.com.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
