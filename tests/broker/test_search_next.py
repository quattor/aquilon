#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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
"""Module for testing the search next command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchNext(TestBrokerCommand):
    """The methods in this class may need to have their values incremented
       as new objects are added.

    """

    def testshortdefault(self):
        command = ["search_next", "--short=aquilon",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "aquilon100.aqd-unittest.ms.com", command)

    def testshortnumber(self):
        command = ["search_next", "--number", "--short=aquilon",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "100", command)
        self.matchclean(out, "aquilon", command)
        self.matchclean(out, ".aqd-unittest.ms.com", command)

    def testshortdefaultmissing(self):
        command = ["search_next", "--short=newseries",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1.aqd-unittest.ms.com", command)

    def testshortnumbermissing(self):
        command = ["search_next", "--number", "--short=newseries",
                   "--dns_domain=aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "1", command)
        self.matchclean(out, "newseries", command)
        self.matchclean(out, ".aqd-unittest.ms.com", command)

    def testmachinedefault(self):
        command = ["search_next", "--machine=evm"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm123", command)

    def testmachinenumber(self):
        command = ["search_next", "--number", "--machine=evm"]
        out = self.commandtest(command)
        self.matchoutput(out, "123", command)
        self.matchclean(out, "evm", command)

    def testmachinedefaultmissing(self):
        command = ["search_next", "--machine=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testmachinenumbermissing(self):
        command = ["search_next", "--number", "--machine=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "1", command)
        self.matchclean(out, "newseries", command)

    def testclusterdefault(self):
        command = ["search_next", "--cluster=utecl"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl14", command)

    def testclusternumber(self):
        command = ["search_next", "--number", "--cluster=utecl"]
        out = self.commandtest(command)
        self.matchoutput(out, "14", command)
        self.matchclean(out, "utecl", command)

    def testclusterdefaultmissing(self):
        command = ["search_next", "--cluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testclusternumbermissing(self):
        command = ["search_next", "--number", "--cluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "1", command)
        self.matchclean(out, "newseries", command)

    def testmetaclusterdefault(self):
        command = ["search_next", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def testmetaclusternumber(self):
        command = ["search_next", "--number", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "8", command)
        self.matchclean(out, "utmc", command)

    def testmetaclusterdefaultmissing(self):
        command = ["search_next", "--metacluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testmetaclusternumbermissing(self):
        command = ["search_next", "--number", "--metacluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "1", command)
        self.matchclean(out, "newseries", command)

    def testnewstart(self):
        command = ["search_next", "--start=9", "--metacluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries9", command)

    def testpackfull(self):
        command = ["search_next", "--pack", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def testpacksparse(self):
        command = ["search_next", "--pack", "--start=0", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc0", command)

    def testpackfullstart(self):
        command = ["search_next", "--pack", "--start=2", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def testpackskiptostart(self):
        command = ["search_next", "--pack", "--start=9", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc9", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNext)
    unittest.TextTestRunner(verbosity=2).run(suite)
