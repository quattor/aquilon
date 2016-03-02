#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014,2015  Contributor
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
"""Module for testing the del personality command."""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand
from broker.personalitytest import PersonalityTestMixin


class TestDelPersonality(PersonalityTestMixin, TestBrokerCommand):

    def test_100_del_utpersonality(self):
        command = ["del_personality", "--personality=utunused/dev",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def test_105_verif_yplenary_dir(self):
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "aquilon", "personality", "utpersonality")
        self.assertFalse(os.path.exists(dir),
                         "Plenary directory '%s' still exists" % dir)

    def test_105_verify_utpersonality(self):
        command = ["show_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        self.notfoundtest(command)

    def test_110_del_eaipersonality(self):
        command = ["del_personality", "--personality=utpers-dev",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def test_120_del_windows_desktop(self):
        command = "del personality --personality desktop --archetype windows"
        self.noouttest(command.split(" "))

    def test_125_verify_windows_desktop(self):
        command = "show personality --personality desktop --archetype windows"
        self.notfoundtest(command.split(" "))

    def test_130_del_badaquilonpersonality(self):
        command = ["del_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def test_135_del_badaquilonpersonality2(self):
        command = ["del_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def test_140_del_esx(self):
        self.drop_personality("vmhost", "esx_server")
        self.drop_personality("vmhost", "vulcan-10g-server-prod")
        self.drop_personality("vmhost", "vulcan-local-disk")
        self.drop_personality("vmhost", "vulcan2-server-dev")
        self.drop_personality("esx_cluster", "vulcan-10g-server-prod")
        self.drop_personality("esx_cluster", "vulcan-local-disk")
        self.drop_personality("esx_cluster", "vulcan2-server-dev")
        self.drop_personality("esx_cluster", "nostage")

    def test_145_del_metacluster(self):
        self.drop_personality("metacluster", "metacluster")
        self.drop_personality("metacluster", "vulcan2")
        self.drop_personality("metacluster", "vulcan-local-disk")

    def test_150_del_camelcase(self):
        self.check_plenary_exists("aquilon", "personality", "camelcase",
                                  "config")
        self.noouttest(["del_personality", "--personality", "CaMeLcAsE",
                        "--archetype", "aquilon"])
        self.check_plenary_gone("aquilon", "personality", "camelcase", "config",
                                directory_gone=True)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
