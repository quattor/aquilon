#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Module for testing the search dns command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestSearchRack(TestBrokerCommand):

    def test_100_byrowcolumn(self):
        command = ["search", "rack", "--row", "k", "--column", "3",
                   "--city", "ny", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "City ny", command)
        self.matchoutput(out, "Row: k", command)
        self.matchoutput(out, "Column: 3", command)
        self.matchclean(out, "City ln", command)

    def test_101_byrack(self):
        command = ["search", "rack", "--rack", "np13"]
        out = self.commandtest(command)
        self.matchoutput(out, "np13", command)

    def test_102_empty_byrack(self):
        command = ["search", "rack", "--rack", "npxx"]
        out = self.noouttest(command)

    def test_103_bybuilding(self):
        command = ["search", "rack", "--building", "np",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Building np", command)
        self.matchclean(out, "Building ut", command)

    def test_104_bycity(self):
        command = ["search", "rack", "--city", "ny",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "City ny", command)
        self.matchclean(out, "City ln", command)

    def test_105_bycountry(self):
        command = ["search", "rack", "--country", "us",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Country us", command)
        self.matchclean(out, "Country tk", command)

    def test_106_byorganization(self):
        command = ["search", "rack", "--organization", "ms",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Organization ms", command)
        self.matchclean(out, "Organization dw", command)

    def test_107_bycontinent(self):
        command = ["search", "rack", "--continent", "na",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Continent na", command)
        self.matchclean(out, "Continent as", command)

    def test_108_byhub(self):
        command = ["search", "rack", "--hub", "ny",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Hub ny", command)
        self.matchclean(out, "Hub ln", command)

    def test_109_bycampus(self):
        command = ["search", "rack", "--campus", "ny",
                   "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Campus ny", command)
        self.matchclean(out, "Campus tk", command)

    def test_110_all(self):
        command = ["search", "rack", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "np13", command)

    def test_111_all_row_column(self):
        command = ["search", "rack", "--all", "--row", "k",
                   "--column", "3", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut13", command)
        self.matchoutput(out, "Row: k", command)
        self.matchoutput(out, "Column: 3", command)

    def test_112_format_raw(self):
        command = ["search", "rack", "--all", "--format", "raw"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut13", command)

    def test_113_format_csv(self):
        command = ["search", "rack", "--all", "--format", "csv"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut13", command)

    def test_114_format_html(self):
        command = ["search", "rack", "--all", "--format", "html"]
        out = self.commandtest(command)
        self.matchoutput(out, ">ut13<", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchRack)
    unittest.TextTestRunner(verbosity=2).run(suite)
