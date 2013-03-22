#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Module for testing the del model command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelModel(TestBrokerCommand):

    def test_100_deluttorswitch(self):
        command = "del model --model uttorswitch --vendor hp"
        self.noouttest(command.split(" "))

    def test_100_verifydeluttorswitch(self):
        command = "show model --model uttorswitch"
        self.notfoundtest(command.split(" "))

    def test_100_delutblade(self):
        command = "del model --model utblade --vendor aurora_vendor"
        self.noouttest(command.split(" "))

    def test_100_verifydelutblade(self):
        command = "show model --model utblade"
        self.notfoundtest(command.split(" "))

    def test_100_delutvirt(self):
        command = ["del", "model", "--model", "default", "--vendor", "utvirt"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Model utvirt/default is still referenced by "
                         "machine models and cannot be deleted.",
                         command)

    def test_110_delutmedium(self):
        command = ["del_model", "--model=utmedium", "--vendor=utvendor"]
        self.noouttest(command)

    def test_120_verifydelutmedium(self):
        command = "show model --model utmedium"
        self.notfoundtest(command.split(" "))

    def test_110_delutlarge(self):
        command = ["del_model", "--model=utlarge", "--vendor=utvendor"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelModel)
    unittest.TextTestRunner(verbosity=2).run(suite)
