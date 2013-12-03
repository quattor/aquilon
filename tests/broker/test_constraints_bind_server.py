#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing constraints involving the bind server command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestBindServerConstraints(TestBrokerCommand):

    def testrejectdelunittest02(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Host unittest00.one-nyp.ms.com still provides "
                         "the following services, and cannot be deleted: "
                         "utsvc/utsi1, utsvc/utsi2.",
                         command)

    # Test that unittest00 comes out of utsi1 but stays in utsi2
    def testunbindutsi1unittest00(self):
        self.noouttest(["unbind", "server",
                        "--hostname", "unittest00.one-nyp.ms.com",
                        "--service", "utsvc", "--instance", "utsi1"])

    def testverifycatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*"unittest02.one-nyp.ms.com"\s*\);',
                          command)

    def testverifyunbindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server Binding: unittest02.one-nyp.ms.com",
                         command)
        self.matchclean(out, "Server Binding: unittest00.one-nyp.ms.com",
                        command)

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*'
                          r'"unittest00.one-nyp.ms.com",\s*'
                          r'"srv-alias.one-nyp.ms.com",\s*'
                          r'"srv-alias2.one-nyp.ms.com",\s*'
                          r'"zebra2.aqd-unittest.ms.com",\s*'
                          r'"unittest00-e1.one-nyp.ms.com"\s*\);',
                          command)

    def testverifyutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server Binding: unittest00.one-nyp.ms.com",
                         command)
        self.matchclean(out, "Server Binding: unittest02.one-nyp.ms.com",
                        command)

    def testrejectdelserviceinstance(self):
        command = "del service --service utsvc --instance utsi2"
        self.badrequesttest(command.split(" "))

    def testrejectdelserverauxiliary(self):
        command = ["del_auxiliary", "--auxiliary", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        # TODO: the error message should be improved
        self.matchoutput(out, "AddressAssignment instance still "
                         "provides the following services, and cannot be "
                         "deleted: utsvc/utsi2.", command)

    def testrejectdelserviceaddress(self):
        command = ["del", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Service Address zebra2 still provides the "
                         "following services, and cannot be deleted: "
                         "utsvc/utsi2.", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServerConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
