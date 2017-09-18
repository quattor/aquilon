#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2015,2016  Contributor
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
"""Module for testing the del required service command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

archetype_required = {
    'aquilon': ["aqd", "bootserver", "dns", "lemon", "ntp", "support-group",
                "syslogng"],
    'esx_cluster': ["esx_management_server"],
    'vmhost': ["dns", "ntp", "syslogng"],
}


class TestDelRequiredService(TestBrokerCommand):

    def test_100_del_required_afs(self):
        command = ["del_required_service", "--service", "afs", "--archetype", "aquilon"] + self.valid_just_tcm
        self.noouttest(command)

    def test_110_del_afs_personality(self):
        self.noouttest(["del_required_service", "--service", "afs",
                        "--archetype", "aquilon",
                        "--personality", "unixeng-test"])
        self.noouttest(["del_required_service", "--service", "afs",
                        "--archetype", "aquilon",
                        "--personality", "utpers-dev"])

        command = ["show_service", "--service", "afs"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'Required for Personality: unixeng-test Archetype: aquilon\s*'
                          r'Stage: current',
                          command)
        self.searchoutput(out,
                          r'Required for Personality: utpers-dev Archetype: aquilon\s*'
                          r'Stage: previous',
                          command)
        self.matchclean(out, "Stage: next", command)

    def test_120_del_required_scope_test(self):
        command = ["del_required_service", "--service=scope_test",
                   "--personality=utpers-dev", "--archetype=aquilon"]
        self.noouttest(command)

        self.noouttest(["promote", "--archetype", "aquilon",
                        "--personality", "utpers-dev"])

    def test_130_del_required_all(self):
        for archetype, services in archetype_required.items():
            for service in services:
                self.noouttest(["del_required_service", "--service", service,
                                "--archetype", archetype] + self.valid_just_tcm)

            command = ["show_archetype", "--archetype", archetype]
            out = self.commandtest(command)
            for service in services:
                self.matchclean(out, "Service: %s" % service, command)

    def test_140_del_chooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            command = ["del_required_service", "--service", service,
                       "--archetype=aquilon", "--personality=unixeng-test"]
            self.noouttest(command)

    def test_145_verify_del_required_personality_next(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test",
                   "--personality_stage", "next"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: chooser1", command)
        self.matchclean(out, "Service: chooser2", command)
        self.matchclean(out, "Service: chooser3", command)

    def test_146_promote(self):
        self.noouttest(["promote", "--archetype", "aquilon",
                        "--personality", "unixeng-test"])

    def test_147_verify_del_required_personality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=unixeng-test"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: chooser1", command)
        self.matchclean(out, "Service: chooser2", command)
        self.matchclean(out, "Service: chooser3", command)

    def test_150_del_required_badpersonality(self):
        command = ["del_required_service", "--service", "badservice",
                   "--archetype=aquilon", "--personality=badpersonality2"]
        self.noouttest(command)

    def test_155_verify_del_required_badpersonality(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=badpersonality2"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: badservice", command)

    def test_160_del_required_esx(self):
        command = ["del_required_service", "--service=esx_management_server",
                   "--archetype=vmhost", "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)
        command = ["del_required_service", "--service=vmseasoning",
                   "--archetype=vmhost", "--personality=vulcan-10g-server-prod"]
        self.noouttest(command)

    def test_165_verify_del_required_esx(self):
        command = ["show_personality",
                   "--archetype=vmhost", "--personality=vulcan-10g-server-prod"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)
        self.matchclean(out, "Service: vmseasoning", command)

        command = ["search_personality", "--archetype=esx_cluster", "--fullinfo"]
        out = self.commandtest(command)
        self.matchclean(out, "Service: esx_management_server", command)

    def test_170_del_required_utsvc(self):
        command = ["del_required_service", "--personality=compileserver",
                   "--service=utsvc", "--archetype=aquilon"]
        self.noouttest(command)

    def test_180_del_required_os(self):
        command = ["del_required_service", "--service", "ips",
                   "--archetype", "aquilon", "--osname", "solaris",
                   "--osversion", "11.1-x86_64"]
        self.noouttest(command)

    def test_200_del_required_afs_again(self):
        command = ["del_required_service", "--service", "afs", "--archetype", "aquilon"] + self.valid_just_tcm
        self.notfoundtest(command)

    def test_200_del_required_personality_again(self):
        command = ["del", "required", "service", "--service", "chooser1",
                   "--archetype=aquilon", "--personality=unixeng-test"]
        self.notfoundtest(command)

    def test_200_del_required_os_again(self):
        command = ["del_required_service", "--service", "ips",
                   "--archetype", "aquilon", "--osname", "solaris",
                   "--osversion", "11.1-x86_64"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Service ips required for operating system "
                         "aquilon/solaris-11.1-x86_64 not found.",
                         command)

    def test_300_cleanup_afs(self):
        # The previous stages still keep the service bound - edit them directly,
        # bypassing the staging workflow
        self.noouttest(["del_required_service", "--service", "afs",
                        "--archetype", "aquilon",
                        "--personality", "unixeng-test",
                        "--personality_stage", "previous"])
        self.noouttest(["del_required_service", "--service", "afs",
                        "--archetype", "aquilon",
                        "--personality", "utpers-dev",
                        "--personality_stage", "previous"])

        command = ["show_service", "--service", "afs"]
        out = self.commandtest(command)
        self.matchclean(out, "Required for", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelRequiredService)
    unittest.TextTestRunner(verbosity=2).run(suite)
