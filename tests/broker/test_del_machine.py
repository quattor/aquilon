#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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

import unittest
from brokertest import TestBrokerCommand
from eventstest import EventsTestMixin


class TestDelMachine(EventsTestMixin, TestBrokerCommand):

    def testdelut3c5n10(self):
        self.check_plenary_exists("machine", "americas", "ut", "ut3",
                                  "ut3c5n10")
        self.event_del_hardware('ut3c5n10')
        command = "del machine --machine ut3c5n10"
        self.noouttest(command.split(" "))
        self.events_verify()
        self.check_plenary_gone("machine", "americas", "ut", "ut3", "ut3c5n10")

    def testverifydelut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n3(self):
        self.event_del_hardware('ut3c1n3')
        command = "del machine --machine ut3c1n3"
        self.noouttest(command.split(" "))
        self.events_verify()

    def testverifydelut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n4(self):
        self.event_del_hardware('ut3c1n4')
        command = "del machine --machine ut3c1n4"
        self.noouttest(command.split(" "))
        self.events_verify()

    def testverifydelut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n9(self):
        self.event_del_hardware('ut3c1n9')
        command = "del machine --machine ut3c1n9"
        self.noouttest(command.split(" "))
        self.events_verify()

    def testdelverariut8(self):
        # The first 3 are deleted in test_del_host
        for port in range(4, 6):
            machine = "ut8s02p%d" % port
            self.event_del_hardware(machine)
            self.noouttest(["del_machine", "--machine", machine])
            self.notfoundtest(["show_machine", "--machine", machine])
            self.events_verify()

    # FIXME: Add a test for deleting a machine with only auxiliaries.

    def testdeljack(self):
        self.event_del_hardware('jack')
        self.noouttest(["del", "machine", "--machine", "jack"])
        self.events_verify()

    def testverifyjackplenary(self):
        # This was the only machine in the building, so the plenary directory
        # should be gone
        dir = os.path.join(self.config.get("broker", "plenarydir"),
                           "machine", "americas", "cards")
        self.assertFalse(os.path.exists(dir),
                         "Plenary directory '%s' still exists" % dir)

    def testdelut3c5n6(self):
        self.event_del_hardware('ut3c5n6')
        self.noouttest(["del", "machine", "--machine", "ut3c5n6"])
        self.events_verify()

    def testdelutnorack(self):
        self.event_del_hardware('utnorack')
        self.noouttest(["del", "machine", "--machine", "utnorack"])
        self.events_verify()

    def testdelnyaqd1(self):
        self.event_del_hardware('ny00l4as01')
        self.noouttest(["del_machine", "--machine", "ny00l4as01"])
        self.events_verify()

    def testdelaurorawithnode(self):
        self.event_del_hardware(self.aurora_with_node)
        self.noouttest(["del_machine", "--machine", self.aurora_with_node])
        self.events_verify()

    def testdelaurorawithoutnode(self):
        self.event_del_hardware(self.aurora_without_node)
        self.noouttest(["del_machine", "--machine", self.aurora_without_node])
        self.events_verify()

    def testdelaurorawithoutrack(self):
        self.event_del_hardware(self.aurora_without_rack)
        self.noouttest(["del_machine", "--machine", self.aurora_without_rack])
        self.events_verify()

    def testaddut3s01p2(self):
        self.event_del_hardware('ut3s01p2')
        self.noouttest(["del", "machine", "--machine", "ut3s01p2"])
        self.events_verify()

    def testverifyall(self):
        self.noouttest(["show_machine", "--all"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
