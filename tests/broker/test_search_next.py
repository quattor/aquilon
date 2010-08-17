#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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

    def testshortfullname(self):
        command = ["search_next", "--fullname", "--short=aquilon",
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

    def testshortfullnamemissing(self):
        command = ["search_next", "--fullname", "--short=newseries",
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

    def testmachinefullname(self):
        command = ["search_next", "--fullname", "--machine=evm"]
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

    def testmachinefullnamemissing(self):
        command = ["search_next", "--fullname", "--machine=newseries"]
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
        self.matchoutput(out, "utecl13", command)

    def testclusterfullname(self):
        command = ["search_next", "--fullname", "--cluster=utecl"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl13", command)

    def testclusternumber(self):
        command = ["search_next", "--number", "--cluster=utecl"]
        out = self.commandtest(command)
        self.matchoutput(out, "13", command)
        self.matchclean(out, "utecl", command)

    def testclusterdefaultmissing(self):
        command = ["search_next", "--cluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testclusterfullnamemissing(self):
        command = ["search_next", "--fullname", "--cluster=newseries"]
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
        self.matchoutput(out, "utmc7", command)

    def testmetaclusterfullname(self):
        command = ["search_next", "--fullname", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc7", command)

    def testmetaclusternumber(self):
        command = ["search_next", "--number", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "7", command)
        self.matchclean(out, "utmc", command)

    def testmetaclusterdefaultmissing(self):
        command = ["search_next", "--metacluster=newseries"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testmetaclusterfullnamemissing(self):
        command = ["search_next", "--fullname", "--metacluster=newseries"]
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
        self.matchoutput(out, "utmc7", command)

    def testpacksparse(self):
        command = ["search_next", "--pack", "--start=0", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc0", command)

    def testpackfullstart(self):
        command = ["search_next", "--pack", "--start=2", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc7", command)

    def testpackskiptostart(self):
        command = ["search_next", "--pack", "--start=9", "--metacluster=utmc"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc9", command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNext)
    unittest.TextTestRunner(verbosity=2).run(suite)
