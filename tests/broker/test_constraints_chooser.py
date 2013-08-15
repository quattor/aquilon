#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
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
"""Testing constraints in the reconfigure section was getting unweildy."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestChooserConstraints(TestBrokerCommand):

    def test_000_setupservice(self):
        command = "add service --service chooser_test --instance max_clients"
        self.noouttest(command.split(" "))

        command = ["update_service", "--service=chooser_test",
                   "--instance=max_clients", "--max_clients=1"]
        self.noouttest(command)

        command = ["map_service", "--service=chooser_test",
                   "--instance=max_clients", "--building=ut"]
        self.noouttest(command)

    def test_010_setuphost(self):
        # Bind a host to that instance
        command = ["bind_client", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--service=chooser_test", "--instance=max_clients"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "aquilon61.aqd-unittest.ms.com adding binding for "
                         "service instance chooser_test/max_clients",
                         command)

    def test_100_failmaxclients(self):
        # Try to bind a second host to that instance
        command = ["bind_client", "--hostname=aquilon62.aqd-unittest.ms.com",
                   "--service=chooser_test", "--instance=max_clients"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The available instances ['max_clients'] for service "
                         "chooser_test are at full capacity.",
                         command)

    def test_110_rebind(self):
        # Rebind the first host - should be no change/errors
        # This is for coverage to check the edge condition.
        command = ["rebind_client", "--hostname=aquilon61.aqd-unittest.ms.com",
                   "--service=chooser_test"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)
        self.matchclean(err, "removing binding", command)
        self.matchclean(err, "adding binding", command)

    def test_120_verifyrebind(self):
        command = ["show_host", "--hostname=aquilon61.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Uses Service: chooser_test Instance: max_clients",
                         command)

    def test_200_cleanuphost(self):
        command = ["reconfigure", "--hostname=aquilon61.aqd-unittest.ms.com"]
        (out, err) = self.successtest(command)
        self.assertEmptyOut(out, command)
        self.matchoutput(err,
                         "aquilon61.aqd-unittest.ms.com removing binding for "
                         "service instance chooser_test/max_clients",
                         command)

    def test_210_cleanupservice(self):
        command = ["unmap_service", "--building=ut",
                   "--service=chooser_test", "--instance=max_clients"]
        self.noouttest(command)

        command = "del service --service chooser_test --instance max_clients"
        self.noouttest(command.split(" "))

        command = "del service --service chooser_test"
        self.noouttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestChooserConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
