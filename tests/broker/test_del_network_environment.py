#!/usr/bin/env python2.6
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
"""Module for testing the del_network_environment command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelNetworkEnvironment(TestBrokerCommand):

    def testdelexcx(self):
        command = ["del", "network", "environment",
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testdelutcolo(self):
        command = ["del", "network", "environment",
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def testdelcardenv(self):
        command = ["del", "network", "environment",
                   "--network_environment", "cardenv"]
        self.noouttest(command)

    def testdelinternal(self):
        command = ["del", "network", "environment",
                   "--network_environment", "internal"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Network Environment internal is the default network "
                         "environment, therefore it cannot be deleted.",
                         command)

    def testverifyexcx(self):
        command = ["show", "network", "environment",
                   "--network_environment", "excx"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Network Environment excx not found.", command)

    def testverifyall(self):
        command = ["show", "network", "environment", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "excx", command)
        self.matchclean(out, "utcolo", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelNetworkEnvironment)
    unittest.TextTestRunner(verbosity=2).run(suite)
