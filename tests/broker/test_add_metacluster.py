#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the add metacluster command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from personalitytest import PersonalityTestMixin


class TestAddMetaCluster(PersonalityTestMixin, TestBrokerCommand):

    def testaddpersonality(self):
        # The broker currently assumes this personality to exist
        self.create_personality("metacluster", "metacluster",
                                grn="grn:/ms/ei/aquilon/aqd")

    def testaddutmc1(self):
        command = ["add_metacluster", "--metacluster=utmc1",
                   "--domain=unittest", "--building=ut"]
        self.noouttest(command)

    def testverifyutmc1(self):
        command = "show metacluster --metacluster utmc1"
        out = self.commandtest(command.split(" "))
        default_members = self.config.get("archetype_metacluster",
                                          "max_members_default")
        self.matchoutput(out, "MetaCluster: utmc1", command)
        self.matchoutput(out, "Max members: %s" % default_members, command)
        self.matchclean(out, "Comments", command)
        self.matchclean(out, "Member:", command)
        self.matchclean(out, "Share:", command)
        self.matchoutput(out, "Domain: unittest", command)
        self.matchoutput(out, "Build Status: build", command)

    def testfailaddexisting(self):
        command = ["add_metacluster", "--metacluster=utmc1",
                   "--building=ut", "--domain=unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Metacluster utmc1 already exists.", command)

    def testaddutmc2(self):
        command = ["add_metacluster", "--metacluster=utmc2",
                   "--max_members=99", "--building=ut",
                   "--domain=unittest",
                   "--comments", "MetaCluster with a comment"]
        self.noouttest(command)

    def testverifyutmc2(self):
        command = "show metacluster --metacluster utmc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc2", command)
        self.matchoutput(out, "Max members: 99", command)
        self.matchoutput(out, "Comments: MetaCluster with a comment", command)

    def testaddutmc3(self):
        command = ["add_metacluster", "--metacluster=utmc3",
                   "--max_members=0", "--building=ut", "--domain=unittest",
                   "--comments", "MetaCluster with no members allowed"]
        self.noouttest(command)

    def testverifyutmc3(self):
        command = "show metacluster --metacluster utmc3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "MetaCluster: utmc3", command)
        self.matchoutput(out, "Max members: 0", command)
        self.matchoutput(out, "Comments: MetaCluster with no members allowed",
                         command)

    def testaddutmc4(self):
        # Sort of a mini-10 Gig design for port group testing...
        command = ["add_metacluster", "--metacluster=utmc4",
                   "--max_members=6", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def testaddutmc5(self):
        # High availability testing
        command = ["add_metacluster", "--metacluster=utmc5",
                   "--max_members=6", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def testaddutmc6(self):
        # High availability testing
        command = ["add_metacluster", "--metacluster=utmc6",
                   "--max_members=6", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def testaddutmc7(self):
        # Test moving machines between metaclusters
        command = ["add_metacluster", "--metacluster=utmc7", "--building=ut",
                   "--domain=unittest"]
        self.noouttest(command)

    def testaddutsandbox(self):
        # Test moving machines between metaclusters
        command = ["add_metacluster", "--metacluster=sandboxmc", "--building=ut",
                   "--sandbox=%s/utsandbox" % self.user]
        self.noouttest(command)

    def testaddvulcan1(self):
        # this should be removed when virtbuild supports new options
        command = ["add_metacluster", "--metacluster=vulcan1"]
        self.noouttest(command)

    def testverifyshowall(self):
        command = "show metacluster --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "utmc1", command)
        self.matchoutput(out, "utmc2", command)
        self.matchoutput(out, "utmc3", command)

    def testnotfoundmetacluster(self):
        command = "show metacluster --metacluster metacluster-does-not-exist"
        self.notfoundtest(command.split(" "))

    def testfailglobal(self):
        command = ["add_metacluster", "--metacluster=global", "--building=ut",
                   "--domain=unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "name global is reserved", command)

    def testbadlocation(self):
        command = ["add_metacluster", "--metacluster=uscluster",
                   "--country=us"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Country us is not within "
                         "a campus.", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
