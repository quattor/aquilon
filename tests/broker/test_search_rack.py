#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the search dns command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
