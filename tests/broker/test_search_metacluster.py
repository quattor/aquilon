#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016,2017  Contributor
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
"""Module for testing the search metacluster command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchMetaCluster(TestBrokerCommand):

    def testarchetypeavailable(self):
        command = "search metacluster --archetype metacluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchoutput(out, "utmc2", command)
        self.matchoutput(out, "hamc1", command)
        self.matchclean(out, "utvcs1", command)
        self.matchclean(out, "utecl1", command)

    def testarchetypeunavailable(self):
        command = "search metacluster --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist not found",
                         command)

    def testbuildstatusavailable(self):
        command = "search metacluster --buildstatus build"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc2", command)
        self.matchclean(out, "utmc1", command)

    def testbuildstatusunavailable(self):
        command = "search metacluster --buildstatus status-does-not-exist"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Unknown cluster lifecycle 'status-does-not-exist'",
                         command)

    def testpersonalityavailable(self):
        command = "search metacluster --personality metacluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "sandboxmc", command)
        self.matchoutput(out, "utmc1", command)
        self.matchoutput(out, "utmc2", command)
        self.matchoutput(out, "utmc4", command)
        self.matchoutput(out, "utmc7", command)
        self.matchoutput(out, "hamc1", command)

    def testpersonalityunavailable1(self):
        command = ['search', 'metacluster', '--archetype', 'metacluster',
                   '--personality', 'personality-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype metacluster not found.", command)

    def testpersonalityunavailable2(self):
        command = "search metacluster --personality personality-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Personality personality-does-not-exist "
                         "not found.", command)

    def testsandboxavailable(self):
        command = ["search_metacluster", "--sandbox=%s/utsandbox" % self.user]
        out = self.commandtest(command)
        self.matchoutput(out, "sandboxmc", command)
        self.matchclean(out, "utmc1", command)

    def testdomainavailable(self):
        command = ["search_metacluster", "--domain=unittest"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc1", command)
        self.matchclean(out, "sandboxmc", command)

    def testdomainunavailable(self):
        command = ["search_metacluster", "--domain=domaind-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Domain domaind-does-not-exist not found.", command)

    def testclusterlocationavailable(self):
        command = "search metacluster --metacluster_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchclean(out, "hamc1", command)

    def testclusterlocationunavailable(self):
        command = ["search_metacluster",
                   "--metacluster_building=bldg-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Building bldg-not-exist not found",
                         command)

    def testallowedpersonalityavailable(self):
        command = "search metacluster --allowed_personality vulcan-10g-server-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchclean(out, "utmc2", command)

    def testallowedpersonalityunavailable(self):
        command = ['search', 'metacluster',
                   '--allowed_personality', 'personality-does-not-exist']
        self.notfoundtest(command)

    def testallowedarchetypeavailable(self):
        command = "search metacluster --allowed_archetype esx_cluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchclean(out, "utmc2", command)

    def testallowedarchetypeunavailable(self):
        command = "search metacluster --allowed_archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype archetype-does-not-exist not found.",
                         command)

    def testmaxmembers(self):
        command = "search metacluster --max_members 99"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc2", command)
        self.matchclean(out, "utmc1", command)
        self.matchclean(out, "utmc3", command)
        self.matchclean(out, "utmc4", command)

    def testmemberarchetype(self):
        command = "search metacluster --member_archetype esx_cluster"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        # We don't have any other metaclusters yet

    def testmemberarchetypeunavailable(self):
        command = "search metacluster --member_archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype archetype-does-not-exist not found.",
                         command)

    def testmemberpersonalityandarchetypeunavailable(self):
        command = ['search', 'metacluster', '--member_archetype', 'hacluster',
                   '--member_personality', 'vulcan-10g-server-prod']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Personality vulcan-10g-server-prod, "
                         "archetype hacluster not found.",
                         command)

    def testmemberpersonality(self):
        command = "search metacluster --member_personality vulcan-10g-server-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchclean(out, "hamc1", command)

    def testmemberpersonalityunavailable(self):
        command = ['search', 'metacluster',
                   '--member_personality', 'personality-does-not-exist']
        self.notfoundtest(command)

    def testvmhostlocationbuilding(self):
        command = "search metacluster --member_building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchoutput(out, "utmc2", command)
        self.matchclean(out, "hamc1", command)

    def testshare(self):
        command = ["search_metacluster", "--share", "test_v2_share"]
        out = self.commandtest(command)
        self.matchoutput(out, "utmc8", command)

    def testshareunavailable(self):
        command = ['search', 'metacluster', '--share', 'share-does-not-exist']
        out = self.notfoundtest(command)
        self.matchoutput(out,
                         "Share share-does-not-exist not found.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchMetaCluster)
    unittest.TextTestRunner(verbosity=5).run(suite)
