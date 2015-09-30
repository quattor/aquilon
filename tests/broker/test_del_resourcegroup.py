#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Module for testing the del resourcegroup command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestDelResourceGroup(TestBrokerCommand):

    def test_100_del_utvcs1(self):
        # Check that the plenaries of contained resources get cleaned up
        rg_base = ["resource", "cluster", "utvcs1", "resourcegroup",
                   "utvcs1as1"]

        rg_path = rg_base[:]
        rg_path.append("config")

        fs_path = rg_base[:]
        fs_path.extend(["filesystem", "fs1", "config"])

        # Verify that we got the paths right
        self.check_plenary_exists(*fs_path)
        self.check_plenary_exists(*rg_path)

        command = ["del_resourcegroup", "--resourcegroup=utvcs1as1",
                   "--cluster=utvcs1"]
        self.successtest(command)

        # The resource plenaries should be gone, and the directory too
        self.check_plenary_gone(*fs_path, directory_gone=True)
        self.check_plenary_gone(*rg_path, directory_gone=True)

    def test_110_del_utmc8_rgs(self):
        command = ["del_resourcegroup", "--resourcegroup=utmc8as1",
                   "--metacluster=utmc8"]
        self.noouttest(command)

        command = ["del_resourcegroup", "--resourcegroup=utmc8as2",
                   "--metacluster=utmc8"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelResourceGroup)
    unittest.TextTestRunner(verbosity=2).run(suite)
