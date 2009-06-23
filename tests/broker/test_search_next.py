#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

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
        self.matchoutput(out, "evm2", command)

    def testmachinefullname(self):
        command = ["search_next", "--fullname", "--machine=evm"]
        out = self.commandtest(command)
        self.matchoutput(out, "evm2", command)

    def testmachinenumber(self):
        command = ["search_next", "--number", "--machine=evm"]
        out = self.commandtest(command)
        self.matchoutput(out, "2", command)
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
        command = ["search_next", "--cluster=utecl", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl4", command)

    def testclusterfullname(self):
        command = ["search_next", "--fullname",
                   "--cluster=utecl", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "utecl4", command)

    def testclusternumber(self):
        command = ["search_next", "--number",
                   "--cluster=utecl", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "4", command)
        self.matchclean(out, "utecl", command)

    def testclusterdefaultmissing(self):
        command = ["search_next", "--cluster=newseries", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testclusterfullnamemissing(self):
        command = ["search_next", "--fullname",
                   "--cluster=newseries", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "newseries1", command)

    def testclusternumbermissing(self):
        command = ["search_next", "--number",
                   "--cluster=newseries", "--cluster_type=esx"]
        out = self.commandtest(command)
        self.matchoutput(out, "1", command)
        self.matchclean(out, "newseries", command)

    def testmetaclusterdefault(self):
        command = ["search_next", "--metacluster=namc"]
        out = self.commandtest(command)
        self.matchoutput(out, "namc3", command)

    def testmetaclusterfullname(self):
        command = ["search_next", "--fullname", "--metacluster=namc"]
        out = self.commandtest(command)
        self.matchoutput(out, "namc3", command)

    def testmetaclusternumber(self):
        command = ["search_next", "--number", "--metacluster=namc"]
        out = self.commandtest(command)
        self.matchoutput(out, "3", command)
        self.matchclean(out, "namc", command)

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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchNext)
    unittest.TextTestRunner(verbosity=2).run(suite)
