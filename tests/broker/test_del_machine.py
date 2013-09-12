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
"""Module for testing the del machine command."""

import os.path

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelMachine(TestBrokerCommand):

    def testdelut3c5n10(self):
        command = "del machine --machine ut3c5n10"
        self.noouttest(command.split(" "))

    def testverifydelut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        self.notfoundtest(command.split(" "))

    # Copy of ut3c5n10, for network based service mappings
    def testdelut3c5n11(self):
        command = "del machine --machine ut3c5n11"
        self.noouttest(command.split(" "))

    def testverifydelut3c5n11(self):
        command = "show machine --machine ut3c5n11"
        self.notfoundtest(command.split(" "))

    # Copy of ut3c5n10, for network / pers based service mappings
    def testdelut3c5n12(self):
        command = "del machine --machine ut3c5n12"
        self.noouttest(command.split(" "))

    def testverifydelut3c5n12(self):
        command = "show machine --machine ut3c5n12"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n3(self):
        command = "del machine --machine ut3c1n3"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n4(self):
        command = "del machine --machine ut3c1n4"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n8(self):
        command = "del machine --machine ut3c1n8"
        self.noouttest(command.split(" "))

    def testdelut3c1n9(self):
        command = "del machine --machine ut3c1n9"
        self.noouttest(command.split(" "))

    def testdelut3s01p1(self):
        command = "del machine --machine ut3s01p1"
        self.noouttest(command.split(" "))

    def testverifydelut3s01p1(self):
        command = "show machine --machine ut3s01p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p1(self):
        command = "del machine --machine ut8s02p1"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p1(self):
        command = "show machine --machine ut8s02p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p2(self):
        command = "del machine --machine ut8s02p2"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p2(self):
        command = "show machine --machine ut8s02p2"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p3(self):
        command = "del machine --machine ut8s02p3"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p3(self):
        command = "show machine --machine ut8s02p3"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p4(self):
        command = "del machine --machine ut8s02p4"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p4(self):
        command = "show machine --machine ut8s02p4"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p5(self):
        command = "del machine --machine ut8s02p5"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p5(self):
        command = "show machine --machine ut8s02p5"
        self.notfoundtest(command.split(" "))

    def testdelhprack(self):
        for i in range(51, 100):
            port = i - 50
            command = "del machine --machine ut9s03p%d" % port
            self.noouttest(command.split(" "))

    def testverifydelhprack(self):
        for i in range(51, 100):
            port = i - 50
            command = "show machine --machine ut9s03p%d" % port
            self.notfoundtest(command.split(" "))

    def testdelverarirack(self):
        for i in range(101, 150):
            port = i - 100
            command = "del machine --machine ut10s04p%d" % port
            self.noouttest(command.split(" "))

    def testverifydelverarirack(self):
        for i in range(101, 150):
            port = i - 100
            command = "show machine --machine ut10s04p%d" % port
            self.notfoundtest(command.split(" "))

    def testdel10gigracks(self):
        for port in range(1, 13):
            command = "del machine --machine ut11s01p%d" % port
            self.noouttest(command.split(" "))
            command = "del machine --machine ut12s02p%d" % port
            self.noouttest(command.split(" "))

    def testdelharacks(self):
        # Machines for metacluster high availability testing
        for port in range(1, 25):
            for rack in ["ut13", "np13"]:
                machine = "%ss03p%d" % (rack, port)
                self.noouttest(["del_machine", "--machine", machine])

    # FIXME: Add a test for deleting a machine with only auxiliaries.

    def testdelut3c5n2(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n2"])

    def testdelut3c5n3(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n3"])

    def testdelut3c5n4(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n4"])

    def testdelut3c5n5(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n5"])

    def testdelnp3c5n5(self):
        self.noouttest(["del", "machine", "--machine", "np3c5n5"])

    def testdeljack(self):
        self.noouttest(["del", "machine", "--machine", "jack"])

    def testverifyjackplenary(self):
        # This was the only machine in the building, so the plenary directory
        # should be gone
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "machine", "americas", "cards")
        self.failIf(os.path.exists(dir),
                    "Plenary directory '%s' still exists" % dir)

    def testdelut3c5n6(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n6"])

    def testdelut3c5n7(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n7"])

    def testdelut3c5n8(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n8"])

    def testdelfiler(self):
        self.noouttest(["del", "machine", "--machine", "filer1"])

    def testdelf5test(self):
        self.noouttest(["del", "machine", "--machine", "f5test"])

    def testdelutnorack(self):
        self.noouttest(["del", "machine", "--machine", "utnorack"])

    def testdelnyaqd1(self):
        self.noouttest(["del_machine", "--machine", "ny00l4as01"])

    def testdelaurorawithnode(self):
        self.noouttest(["del_machine", "--machine", self.aurora_with_node])

    def testdelaurorawithoutnode(self):
        self.noouttest(["del_machine", "--machine", self.aurora_without_node])

    def testdelaurorawithoutrack(self):
        self.noouttest(["del_machine", "--machine", self.aurora_without_rack])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
