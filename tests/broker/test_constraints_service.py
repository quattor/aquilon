#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013  Contributor
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
"""Module for testing constraints in commands involving domain."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestServiceConstraints(TestBrokerCommand):

    def testdelrequiredservicepersonalitymissing(self):
        command = ["del_required_service", "--service=ntp",
                   "--archetype=windows", "--personality=desktop"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service ntp required for archetype windows, "
                         "personality desktop not found.", command)

    def testdelservicewithinstances(self):
        command = "del service --service unmapped"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service unmapped still has instances defined "
                         "and cannot be deleted.", command)

    def testdelarchetyperequiredservice(self):
        command = "del service --service aqd"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd is still required by the following "
                         "archetypes: aquilon.", command)

    def testdelpersonalityrequiredservice(self):
        command = "del service --service chooser1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service chooser1 is still required by the "
                         "following personalities: unixeng-test (aquilon).",
                         command)

    def testverifydelservicewithinstances(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd", command)

    def testdelserviceinstancewithservers(self):
        command = "del service --service aqd --instance ny-prod"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd, instance ny-prod is still being "
                         "provided by servers", command)

    def testverifydelserviceinstancewithservers(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def testdelserviceinstancewithclients(self):
        command = "del service --service utsvc --instance utsi1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service utsvc, instance utsi1 still has "
                         "clients and cannot be deleted", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
