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

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestBindServerConstraints(TestBrokerCommand):

    def testrejectdelunittest02(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Cannot delete host unittest00.one-nyp.ms.com due "
                         "to the following dependencies:",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com is bound as a server for "
                         "service utsvc instance utsi1",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com is bound as a server for "
                         "service utsvc instance utsi2",
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
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

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
                          r'"servers" = list\(\s*"unittest00.one-nyp.ms.com"\s*\);',
                          command)

    def testverifyutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)

    def testrejectdelserviceinstance(self):
        command = "del service --service utsvc --instance utsi2"
        self.badrequesttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServerConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
