#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the add personality command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddPersonality(TestBrokerCommand):

    def testaddutpersonality(self):
        command = ["add_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifyaddutpersonality(self):
        command = ["show_personality", "--personality=utpersonality",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchclean(out, "Threshold:", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)

    def testverifyutpersonalitynothreshold(self):
        user = self.config.get("unittest", "user")
        command = ["show_personality", "--sandbox=%s/changetest1" % user,
                   "--archetype=aquilon", "--personality=utpersonality"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: None", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)

    def testverifyshowpersonalityallnothreshold(self):
        user = self.config.get("unittest", "user")
        command = "show personality --all --sandbox %s/changetest1" % user
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: None", command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)
        # Also expecting one of the personalities to have a non-zero threshold.
        self.searchoutput(out, r'Threshold: \d+', command)

    def testverifyutpersonalitythreshold(self):
        command = ["show_personality", "--domain=unittest",
                   "--archetype=aquilon", "--personality=utpersonality"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: 50", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)

    def testverifyshowpersonalityallthreshold(self):
        command = "show personality --all --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: 50", command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)

    def testverifyshowpersonalityall(self):
        command = "show personality --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)
        self.matchclean(out, "Threshold:", command)

    def testverifyshowutpersonalityproto(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=utpersonality", "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality")
        self.failUnlessEqual(personality.threshold, -1)

    def testverifyshowpersonalityallproto(self):
        command = "show personality --all --format=proto"
        out = self.commandtest(command.split(" "))
        pl = self.parse_personality_msg(out)
        archetypes = {}
        found_threshold = False
        for personality in pl.personalities:
            archetype = personality.archetype.name
            if archetype in archetypes:
                archetypes[archetype][personality.name] = personality
            else:
                archetypes[archetype] = {personality.name:personality}
            if personality.threshold >= 0:
                found_threshold = True
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality" in archetypes["aquilon"],
                        "No aquilon/utpersonality in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality"].threshold,
                             -1,
                             "Got threshold %s for aquilon/utpersonality" %
                             archetypes["aquilon"]["utpersonality"].threshold)
        self.failIf(found_threshold,
                    "Found a threshold defined when none expected.")

    def testverifyshowutpersonalityprotonothreshold(self):
        user = self.config.get("unittest", "user")
        command = ["show_personality", "--sandbox=%s/changetest1" % user,
                   "--archetype=aquilon", "--personality=utpersonality",
                   "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality")
        self.failUnlessEqual(personality.threshold, -1)

    def testverifyshowpersonalityallprotonothreshold(self):
        user = self.config.get("unittest", "user")
        command = ["show_personality", "--all",
                   "--sandbox=%s/changetest1" % user, "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out)
        archetypes = {}
        found_threshold = False
        for personality in pl.personalities:
            archetype = personality.archetype.name
            if archetype in archetypes:
                archetypes[archetype][personality.name] = personality
            else:
                archetypes[archetype] = {personality.name:personality}
            if personality.threshold >= 0:
                found_threshold = True
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality" in archetypes["aquilon"],
                        "No aquilon/utpersonality in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality"].threshold,
                             -1,
                             "Got threshold %s for aquilon/utpersonality" %
                             archetypes["aquilon"]["utpersonality"].threshold)
        self.failUnless(found_threshold,
                        "No thresholds defined in sandbox changetest1.")

    def testverifyshowutpersonalityprotothreshold(self):
        command = ["show_personality", "--domain=unittest",
                   "--archetype=aquilon", "--personality=utpersonality",
                   "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality")
        self.failUnlessEqual(personality.threshold, 50)

    def testverifyshowpersonalityallprotothreshold(self):
        command = "show personality --all --domain unittest --format=proto"
        out = self.commandtest(command.split(" "))
        pl = self.parse_personality_msg(out)
        archetypes = {}
        for personality in pl.personalities:
            archetype = personality.archetype.name
            if archetype in archetypes:
                archetypes[archetype][personality.name] = personality
            else:
                archetypes[archetype] = {personality.name:personality}
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality" in archetypes["aquilon"],
                        "No aquilon/utpersonality in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality"].threshold,
                             50,
                             "Got threshold %s for aquilon/utpersonality" %
                             archetypes["aquilon"]["utpersonality"].threshold)

    def testverifyshowpersonalityarchetype(self):
        command = "show personality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/config.tpl",
                         command)
        self.matchoutput(out, "Personality: inventory Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: aquilon/personality/inventory/config.tpl",
                         command)
        self.matchclean(out, "Personality: generic Archetype: aurora",
                        command)
        self.matchclean(out, "Template: aurora/personality/generic/config.tpl",
                        command)

    def testshowarchetypeunavailable(self):
        command = "show personality --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowarchetypeunavailable2(self):
        command = ["show", "personality",
                   "--archetype", "archetype-does-not-exist",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowpersonalityunavailable(self):
        command = ["show", "personality", "--archetype", "aquilon",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype aquilon not found.", command)

    def testshowpersonalityunavailable2(self):
        command = ["show", "personality",
                   "--personality", "personality-does-not-exist"]
        self.noouttest(command)

    def testshowpersonalityname(self):
        command = "show personality --personality generic"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)
        self.matchoutput(out, "Personality: generic Archetype: windows",
                         command)
        self.matchoutput(out,
                         "Template: windows/personality/generic/config.tpl",
                         command)

    def testaddwindowsdesktop(self):
        command = "add personality --personality desktop --archetype windows"
        self.noouttest(command.split(" "))

    def testverifyaddwindowsdesktop(self):
        command = "show personality --personality desktop --archetype windows"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: desktop Archetype: windows",
                         command)
        self.matchoutput(out,
                         "Template: windows/personality/desktop/config.tpl",
                         command)

    def testaddbadaquilonpersonality(self):
        # This personality is 'bad' because there will not be a set of
        # templates defined for it in the repository.
        command = ["add_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifybadaquilonpersonality(self):
        command = ["show_personality", "--personality=badpersonality",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: badpersonality Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/badpersonality/config.tpl",
                         command)

    def testaddbadaquilonpersonality2(self):
        # This personality is double 'bad'... there will be a required
        # service for the personality that has no instances.
        command = ["add_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        self.noouttest(command)

    def testverifybadaquilonpersonality2(self):
        command = ["show_personality", "--personality=badpersonality2",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Personality: badpersonality2 Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/badpersonality2/config.tpl",
                         command)

    def testaddinvalidpersonalityname(self):
        command = ["add_personality", "--personality", "this is a bad; name",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality name 'this is a bad; name' is "
                         "not valid", command)

    def testaddduplicate(self):
        command = ["add_personality", "--personality", "inventory",
                   "--archetype", "aquilon"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality inventory, archetype aquilon "
                         "already exists.", command)

    def testaddesxserver(self):
        command = "add personality --personality esx_server --archetype vmhost"
        self.noouttest(command.split(" "))

    def testaddesxdesktop(self):
        command = ["add_personality",
                   "--personality=esx_desktop", "--archetype=vmhost"]
        self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)

