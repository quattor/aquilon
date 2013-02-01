#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing constraints in commands involving DNS."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDnsConstraints(TestBrokerCommand):

    def testdelenvinuse(self):
        command = ["del", "dns", "environment", "--dns_environment", "ut-env"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "DNS Environment ut-env is still in use by DNS "
                         "records, and cannot be deleted.", command)

    def testdelmappeddomain(self):
        command = ["del", "dns", "domain", "--dns_domain", "new-york.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Domain new-york.ms.com is still mapped to "
                         "locations and cannot be deleted.",
                         command)

    def testdelaliasedaddress(self):
        command = ["del", "address", "--fqdn", "arecord13.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record arecord13.aqd-unittest.ms.com still has "
                         "aliases, delete them first.",
                         command)

    def testdelaliasedalias(self):
        command = ["del", "alias", "--fqdn", "alias2host.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Alias alias2host.aqd-unittest.ms.com still has "
                         "aliases, delete them first.",
                         command)

    def testdelsrvtarget(self):
        command = ["del", "address", "--fqdn", "arecord15.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record arecord15.aqd-unittest.ms.com is still in "
                         "use by SRV records, delete them first.",
                         command)

    def testdelserviceaddress(self):
        ip = self.net.unknown[13].usable[1]
        command = ["del", "address", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "DNS Record zebra2.aqd-unittest.ms.com [%s] is used "
                         "as a service address, therefore it cannot be "
                         "deleted." % ip,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestDnsConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
