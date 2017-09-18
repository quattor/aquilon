#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the del disk command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from eventstest import EventsTestMixin


class TestDelDisk(EventsTestMixin, TestBrokerCommand):

    def test_100_del_ut3c1n3_sda_hostname(self):
        hostname = "unittest00.one-nyp.ms.com"
        command = ["del", "disk", "--hostname", hostname, "--disk", "sda"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Not Found: Host %s not found" % hostname,
                         command)

    def test_101_del_ut3c1n3_sda(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3", "--disk", "sda"])


    def test_105_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "sda", command)
        self.searchoutput(out,
                          r'Disk: c0d1 34 GB cciss \(local\) \[boot\]$',
                          command)

    def test_105_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "sda", command)
        self.searchoutput(out,
                          r'"harddisks/{cciss/c0d1}" = '
                          r'create\("hardware/harddisk/generic/cciss",\s*'
                          r'"boot", true,\s*'
                          r'"bus", "pci:0000:01:00.0",\s*'
                          r'"capacity", 34\*1024,\s*'
                          r'"interface", "cciss"\s*\)',
                          command)

    def test_110_del_ut3c1n3_all(self):
        self.noouttest(["del", "disk", "--machine", "ut3c1n3", "--all"])

    def test_115_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "sda", command)
        self.matchclean(out, "c0d0", command)

    def test_115_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "harddisks", command)

    def test_200_del_ut3c1n3_c0d0(self):
        command = ["del", "disk", "--machine", "ut3c1n3", "--disk", "c0d0"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Disk c0d0, machine ut3c1n3 not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDisk)
    unittest.TextTestRunner(verbosity=2).run(suite)
