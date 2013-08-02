#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the show fqdn command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestShowFqdn(TestBrokerCommand):

    def testshowfqdnall(self):
        command = "show fqdn --all"
        (out, err) = self.successtest(command.split(" "))
        # The aq client does not ask for this...
        #self.matchoutput(err, "The show_fqdn command is deprecated.", command)

        # Chassis
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        # TorSwitch
        self.matchoutput(out, "ut3gd1r01.aqd-unittest.ms.com", command)
        # Aurora Host
        self.matchoutput(out, "pissp1.ms.com", command)
        # Aquilon Host
        self.matchoutput(out, "unittest00.one-nyp.ms.com", command)
        # Auxiliary
        self.matchoutput(out, "unittest00-e1.one-nyp.ms.com", command)
        # Windows Host
        self.matchoutput(out, "unittest01.one-nyp.ms.com", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowFqdn)
    unittest.TextTestRunner(verbosity=2).run(suite)
