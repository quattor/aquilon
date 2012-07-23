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
"""Module for testing the add required service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddRequiredService(TestBrokerCommand):

    def testaddrequiredafs(self):
        command = "add required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testaddrequiredafsduplicate(self):
        command = "add required service --service afs --archetype aquilon"
        command += " --justification tcm=12345678"
        self.badrequesttest(command.split(" "))

    def testaddrequiredafsnojustification(self):
        command = "add required service --service afs --archetype aquilon"
        out = self.unauthorizedtest(command.split(" "), auth=True,
                                    msgcheck=False)
        self.matchoutput(out,
                         "Changing the required services of an archetype "
                         "requires --justification.",
                         command)

    def testfailmissingservice(self):
        command = ["add_required_service", "--service",
                   "does-not-exist", "--archetype", "aquilon",
                   "--justification", "tcm=12345678"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service does-not-exist not found.",
                         command)

    def testaddrequireddns(self):
        command = "add required service --service dns --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testaddrequiredaqd(self):
        command = "add required service --service aqd --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testaddrequiredntp(self):
        command = "add required service --service ntp --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testaddrequiredbootserver(self):
        command = ["add_required_service",
                   "--service=bootserver", "--archetype=aquilon",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def testaddrequiredsupportgroup(self):
        self.noouttest(["add_required_service", "--service", "support-group",
                        "--archetype", "aquilon",
                        "--justification", "tcm=12345678"])

    def testaddrequiredlemon(self):
        command = "add required service --service lemon --archetype aquilon"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testverifyaddrequiredservices(self):
        command = "show archetype --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs", command)
        self.matchoutput(out, "Service: aqd", command)
        self.matchoutput(out, "Service: bootserver", command)
        self.matchoutput(out, "Service: dns", command)
        self.matchoutput(out, "Service: ntp", command)
        self.matchoutput(out, "Service: lemon", command)

    def testverifyaddrequiredafs(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Required for Archetype: aquilon", command)

    def testaddrequiredpersonality(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["add_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def testaddrequiredpersonalityduplicate(self):
        command = ["add_required_service", "--service", "chooser1",
                   "--archetype", "aquilon", "--personality", "unixeng-test"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Service chooser1 is already required by "
                         "personality unixeng-test, archetype aquilon.",
                         command)

    def testverifyaddrequiredpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: chooser1", command)
        self.matchoutput(out, "Service: chooser2", command)
        self.matchoutput(out, "Service: chooser3", command)

    def testverifyaddrequiredpersonalitychooser1(self):
        command = "show service --service chooser1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
            "Required for Personality: unixeng-test Archetype: aquilon",
            command)

    def testaddrequiredutsvc(self):
        command = ["add_required_service", "--personality=compileserver",
                   "--service=utsvc", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequiredutsvc(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=compileserver"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: utsvc", command)

    def testaddrequirednetmap(self):
        command = ["add_required_service", "--personality=eaitools",
                   "--service=netmap", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequirednetmap(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=eaitools"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: netmap", command)

    def testaddrequirednetmapcopy(self):
        self.noouttest(["add_personality", "--personality", "testme",
                          "--eon_id", "2", "--archetype", "aquilon",
                          "--copy_from", "eaitools",
                          "--host_environment", "dev"])

        command = ["show_personality", "--archetype=aquilon",
                   "--personality=testme"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: netmap", command)

        self.successtest(["del_personality", "--personality", "testme",
                          "--archetype", "aquilon"])

    def testaddrequiredbadservice(self):
        command = ["add_required_service", "--service=badservice",
                   "--personality=badpersonality2", "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddrequiredbadservice(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: badservice", command)

    def testaddrequiredvmhost(self):
        command = "add required service --service dns --archetype vmhost"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))
        command = "add required service --service ntp --archetype vmhost"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))
        command = "add required service --service syslogng --archetype vmhost"
        command += " --justification tcm=12345678"
        self.noouttest(command.split(" "))

    def testverifyaddrequiredvmhost(self):
        command = "show archetype --archetype vmhost"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: dns", command)
        self.matchoutput(out, "Service: ntp", command)
        self.matchoutput(out, "Service: syslogng", command)
        self.matchclean(out, "Service: afs", command)

    def testaddrequiredesx(self):
        command = ["add_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)
        command = ["add_required_service", "--service=esx_management_server",
                   "--archetype=esx_cluster", "--justification", "tcm=12345678"]
        self.noouttest(command)
        command = ["add_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan2-10g-test"]
        self.noouttest(command)
        command = ["add_required_service", "--service=vmseasoning",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        self.noouttest(command)

    def testverifyaddrequiredesx(self):
        command = ["show_personality",
                   "--archetype=vmhost", "--personality=vulcan-1g-desktop-prod"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: esx_management_server", command)
        self.matchoutput(out, "Service: vmseasoning", command)

        command = ["show_archetype",
                   "--archetype=esx_cluster"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service: esx_management_server", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
