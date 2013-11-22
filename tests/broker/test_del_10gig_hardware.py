#!/usr/bin/env python
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
"""Module for testing commands that remove virtual hardware."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDel10GigHardware(TestBrokerCommand):

    def test_200_del_hosts(self):
        nets = (self.net["ut01ga2s01_v710"], self.net["ut01ga2s01_v711"],
                self.net["ut01ga2s01_v712"], self.net["ut01ga2s01_v713"],
                self.net["ut01ga2s02_v710"], self.net["ut01ga2s02_v711"],
                self.net["ut01ga2s02_v712"], self.net["ut01ga2s02_v713"])
        for i in range(0, 8) + range(9, 16):
            hostname = "ivirt%d.aqd-unittest.ms.com" % (1 + i)
            command = "del_host --hostname %s" % hostname

            if i < 9:
                net_index = (i % 4)
                usable_index = i / 4
            else:
                net_index = ((i - 9) % 4) + 4
                usable_index = (i - 9) / 4
            ip = nets[net_index].usable[usable_index]
            self.dsdb_expect_delete(ip)

            (out, err) = self.successtest(command.split(" "))
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def test_300_delaux(self):
        for i in range(1, 25):
            hostname = "evh%d-e1.aqd-unittest.ms.com" % (i + 50)
            self.dsdb_expect_delete(self.net["vm_storage_net"].usable[i - 1])
            command = ["del", "auxiliary", "--auxiliary", hostname]
            (out, err) = self.successtest(command)
            self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def test_700_delmachines(self):
        for i in range(0, 8) + range(9, 16):
            machine = "evm%d" % (10 + i)
            self.noouttest(["del", "machine", "--machine", machine])

    def test_800_verifydelmachines(self):
        for i in range(0, 18):
            machine = "evm%d" % (10 + i)
            command = "show machine --machine %s" % machine
            self.notfoundtest(command.split(" "))

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDel10GigHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
