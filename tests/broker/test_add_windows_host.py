#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Module for testing the add windows host command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddWindowsHost(TestBrokerCommand):

    def testaddunittest01(self):
        ip = self.net["unknown0"].usable[10]
        mac = self.net["unknown0"].usable[5].mac
        self.dsdb_expect_add("unittest01.one-nyp.ms.com", ip, "eth0", mac)
        self.noouttest(["add", "windows", "host",
                        "--hostname", "unittest01.one-nyp.ms.com",
                        "--ip", ip, "--machine", "ut3c1n4"])
        self.dsdb_verify()

    def testverifyaddunittest01(self):
        command = "show host --hostname unittest01.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Primary Name: unittest01.one-nyp.ms.com [%s]" %
                         self.net["unknown0"].usable[10],
                         command)
        self.matchoutput(out, "Blade: ut3c1n4", command)
        self.matchoutput(out, "Archetype: windows", command)
        self.matchoutput(out, "Personality: generic", command)
        self.matchoutput(out, "Domain: ny-prod", command)
        self.matchoutput(out, "Build Status: build", command)
        self.matchoutput(out, "Advertise Status: False", command)
        self.matchoutput(out, "Operating System: windows", command)
        self.matchoutput(out, "Version: generic", command)
        self.matchoutput(out,
                         "Template: windows/os/windows/generic/config" +
                         self.template_extension,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddWindowsHost)
    unittest.TextTestRunner(verbosity=2).run(suite)
