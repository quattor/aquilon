#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012,2013,2014,2015  Contributor
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
"""Module for testing constraints in commands involving services."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestServiceConstraints(TestBrokerCommand):

    def test_100_del_required_service_personality_missing(self):
        command = ["del_required_service", "--service=ntp",
                   "--archetype=windows", "--personality=desktop"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service ntp is not required for personality "
                         "windows/desktop.", command)

    def test_110_del_service_with_instances(self):
        command = "del service --service unmapped"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service unmapped still has instances defined "
                         "and cannot be deleted.", command)

    def test_115_verify_service_with_instances(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd", command)

    def test_120_del_archetype_required_service(self):
        command = "del service --service aqd"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd is still required by the following "
                         "archetypes: aquilon.", command)

    def test_130_del_personality_required_service(self):
        command = "del service --service chooser1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service chooser1 is still required by the "
                         "following personalities: ", command)

    def test_145_verify_del_service_instance_with_servers(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def test_150_del_service_instance_with_clients(self):
        command = "del service --service utsvc --instance utsi1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service utsvc, instance utsi1 still has "
                         "clients and cannot be deleted", command)

    def test_160_add_required_service_no_justification(self):
        command = "add required service --service utsvc --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "The operation has production impact, "
                         "--justification is required.",
                         command)

    def test_165_del_required_afs_no_justification(self):
        command = "del required service --service afs --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "The operation has production impact, "
                         "--justification is required.",
                         command)

    def test_170_bind_server(self):
        command = ['bind_server', '--service', 'dns', '--instance', 'unittest',
                   '--hostname', 'unittest20.aqd-unittest.ms.com']
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,
                         "The operation has production impact, "
                         "--justification is required.",
                         command)

    def test_175_unbind_server(self):
        command = ['unbind_server', '--service', 'dns',
                   '--instance', 'unittest', '--position', 1]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,
                         "The operation has production impact, "
                         "--justification is required.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
