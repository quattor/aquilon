#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUnbindClient(TestBrokerCommand):

    def test_100_bind_unmapped(self):
        command = ["bind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance unmapped/instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_100_bind_unmapped_unbuilt(self):
        command = ["bind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped", "--instance=instance1"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "aquilon94.aqd-unittest.ms.com adding binding for "
                         "service instance unmapped/instance1",
                         command)
        self.matchclean(err, "removing binding", command)

    def test_200_verify_bind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "unmapped", command)

    def test_200_verify_bind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def test_300_unbind_unmapped(self):
        command = ["unbind_client", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_300_unbind_unmapped_unbuilt(self):
        command = ["unbind_client", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        (out, err) = self.successtest(command)
        self.matchoutput(err,
                         "Warning: Host aquilon94.aqd-unittest.ms.com is "
                         "missing the following required services, please run "
                         "'aq reconfigure': afs, aqd, bootserver, dns, lemon, "
                         "ntp, support-group, syslogng.",
                         command)

    def test_400_verify_unbind_search(self):
        command = ["search_host", "--hostname=unittest02.one-nyp.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_search_unbuilt(self):
        command = ["search_host", "--hostname=aquilon94.aqd-unittest.ms.com",
                   "--service=unmapped"]
        self.noouttest(command)

    def test_400_verify_unbind_cat(self):
        command = ["cat", "--hostname=unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "unmapped", command)

    def test_400_verify_unbind_cat_unbuilt(self):
        command = ["cat", "--hostname=aquilon94.aqd-unittest.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out, "No such file or directory", command)

    def testrejectunbindrequired(self):
        command = "unbind client --hostname unittest02.one-nyp.ms.com --service afs"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Cannot unbind a required service", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
