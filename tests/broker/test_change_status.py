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
"""Module for testing the reconfigure command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestChangeStatus(TestBrokerCommand):
    def testchangeunittest02(self):
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['failed', 'rebuild', 'ready']:
            command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                       "--buildstatus", status]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "1/1 object template", command)

            command = "show host --hostname unittest02.one-nyp.ms.com"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)

            command = "cat --hostname unittest02.one-nyp.ms.com --data"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status, command)

        # And a transition that should be illegal from the final state above (ready)
        command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                   "--buildstatus", "install"]
        self.badrequesttest(command)

    def testchangeunittest03(self):
        # we start off as "ready", so each of these transitions (in order)
        # should be valid
        for status in ['decommissioned', 'rebuild', 'ready']:
            command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                       "--buildstatus", status]
            (out, err) = self.successtest(command)
            self.matchoutput(err, "1/1 object template", command)

            command = "show host --hostname unittest02.one-nyp.ms.com"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Build Status: %s" % status, command)

            command = "cat --hostname unittest02.one-nyp.ms.com --data"
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, '"system/build" = "%s";' % status, command)

        # And a transition that should be illegal from the final state above (ready)
        command = ["change_status", "--hostname=unittest02.one-nyp.ms.com",
                   "--buildstatus", "install"]
        self.badrequesttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestChangeStatus)
    unittest.TextTestRunner(verbosity=2).run(suite)
