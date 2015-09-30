#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2015  Contributor
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
"""Module for testing the del archetype command."""

if __name__ == "__main__":
    from broker import utils
    utils.import_depends()

import unittest
from broker.brokertest import TestBrokerCommand


class TestDelArchetype(TestBrokerCommand):

    def test_100_del_utarchetype1(self):
        command = ["del_archetype", "--archetype=utarchetype1"]
        self.noouttest(command)

    def test_100_del_utarchetype2(self):
        command = ["del_archetype", "--archetype=utarchetype2"]
        self.noouttest(command)

    def test_100_del_utarchetype3(self):
        command = ["del_archetype", "--archetype=utarchetype3"]
        self.noouttest(command)

    def test_105_verif_utarchetype1(self):
        command = ["show_archetype", "--archetype=utarchetype1"]
        self.notfoundtest(command)

    def test_110_del_utappliance(self):
        command = ["del_archetype", "--archetype=utappliance"]
        self.noouttest(command)

    def test_300_verify_all(self):
        command = ["show_archetype", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "utarchetype", command)
        self.matchclean(out, "utappliance", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
