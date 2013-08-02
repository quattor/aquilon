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
"""Module for testing the del cpu command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelCpu(TestBrokerCommand):

    def testdelutcpu(self):
        command = "del cpu --cpu utcpu --vendor intel --speed 1000"
        self.noouttest(command.split(" "))

    def testverifydelutcpu(self):
        command = "show cpu --cpu utcpu --speed 1000 --vendor intel"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Cpu: intel utcpu 1000 MHz", command)

    def testdelutcpu2(self):
        command = "del cpu --cpu utcpu_1500 --vendor intel --speed 1500"
        self.noouttest(command.split(" "))

    def testverifydelutcpu2(self):
        command = "show cpu --cpu utcpu_1500"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Cpu: intel utcpu_1500 1500 MHz", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelCpu)
    unittest.TextTestRunner(verbosity=2).run(suite)
