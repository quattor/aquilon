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
"""Module for testing commands that remove virtual hardware."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelVirtualHardware(TestBrokerCommand):

    def test_200_del_windows_hosts(self):
        command = "del_host --hostname aqddesk1.msad.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def test_300_readd_windows_host(self):
        command = ["add_windows_host", "--hostname=aqdtop1.msad.ms.com",
                   "--machine=evm1", "--comments=Windows Virtual Desktop"]
        self.noouttest(command)

    def test_400_reverify_windows_host(self):
        command = "show host --hostname aqdtop1.msad.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: aqdtop1.msad.ms.com", command)
        self.matchoutput(out, "Virtual_machine: evm1", command)
        self.matchoutput(out, "Comments: Windows Virtual Desktop", command)

    def test_500_redel_windows_hosts(self):
        command = "del_host --hostname aqdtop1.msad.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def test_700_delmachines(self):
        for i in range(1, 10) + \
                 range(50, 63) + range(70, 83) + \
                 range(90, 103) + range(110, 123):
            self.noouttest(["del", "machine", "--machine", "evm%s" % i])

    def test_800_verifydelmachines(self):
        for i in range(1, 10) + \
                 range(50, 63) + range(70, 83) + \
                 range(90, 103) + range(110, 123):
            command = "show machine --machine evm%s" % i
            self.notfoundtest(command.split(" "))

    # Hack... doing this test here for timing reasons...
    def test_900_verifydelclusterwithmachines(self):
        command = "del esx cluster --cluster utecl1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Cluster utecl1 is still in use by hosts",
                         command)

    def test_800_verifycatcluster(self):
        command = "cat --cluster=utecl1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template clusters/utecl1;", command)
        self.searchoutput(out,
                          r'include { "service/esx_management_server/ut.[ab]/client/config" };',
                          command)

        command = "cat --cluster=utecl1 --data"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"system/cluster/name" = "utecl1";', command)
        self.matchoutput(out, '"system/metacluster/name" = "utmc1";', command)
        self.matchclean(out, "resources/virtual_machine", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelVirtualHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
