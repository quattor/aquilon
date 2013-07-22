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
"""Module for testing the del service address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelServiceAddress(TestBrokerCommand):

    def testdelzebra2(self):
        ip = self.net["unknown13"].usable[1]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def testdelzebra2again(self):
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service Address zebra2, hostresource instance "
                         "not found.", command)
        self.dsdb_verify(empty=True)

    def testverifyzebra2(self):
        command = ["show", "address", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "DNS Record zebra2.aqd-unittest.ms.com not "
                         "found.", command)

    def testdelzebra3(self):
        ip = self.net["unknown13"].usable[0]
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", ip)
        command = ["del", "service", "address", "--keep_dns",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--name", "zebra3"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyzebra3(self):
        ip = self.net["unknown13"].usable[0]
        command = ["show", "address", "--fqdn", "zebra3.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "DNS Record: zebra3.aqd-unittest.ms.com", command)
        self.matchoutput(out, "IP: %s" % ip, command)
        self.matchclean(out, "Assigned To", command)
        self.matchclean(out, "ut3c5n2", command)
        self.matchclean(out, "eth0", command)

    def testdelzebra3again(self):
        command = ["del", "service", "address", "--name", "zebra3",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service Address zebra3, hostresource instance "
                         "not found.", command)
        self.dsdb_verify(empty=True)

    def testfailhostname(self):
        command = ["del", "service", "address", "--name", "hostname",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "The primary address of the host cannot be "
                         "deleted.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
