#!/usr/bin/env python2.6
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
"""Module for testing the ping command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPing(TestBrokerCommand):

    def testping(self):
        command = "ping"
        out = self.commandtest(command)
        self.matchoutput(out, "pong", command)

    def testpingnoauth(self):
        command = "ping"
        out = self.commandtest(command, auth=False)
        self.matchoutput(out, "pong", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPing)
    unittest.TextTestRunner(verbosity=2).run(suite)
