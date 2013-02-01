#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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

GRN = "grn:/ms/ei/aquilon/aqd"


class TestAddPersonality(TestBrokerCommand):

    def testaddaqdgrns(self):
        command = ["add", "grn", "--grn", GRN, "--eon_id", 2]
        self.noouttest(command)

    def testaddutpersonality(self):
        command = ["add_personality", "--personality=utpersonality/dev",
                   "--archetype=aquilon", "--grn=%s" % GRN, "--config_override",
                   "--host_environment=dev",
                   "--comments", "Some personality comments"]
        self.noouttest(command)
        self.verifycatforpersonality("aquilon", "utpersonality/dev", True, "dev")

    def testverifyaddutpersonality(self):
        command = ["show_personality", "--personality=utpersonality/dev",
                   "--archetype=aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
                         command)
        self.matchoutput(out, "Config override: enabled", command)
        self.matchoutput(out, "Environment: dev", command)
        self.matchoutput(out, "Comments: Some personality comments", command)
        self.matchclean(out, "Threshold:", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)
        self.matchoutput(out, "GRN: %s" % GRN, command)

    def testaddeaipersonality(self):
        command = ["add_personality", "--personality=eaitools",
                   "--archetype=aquilon", "--eon_id=2",
                   "--host_environment=legacy",
                   "--comments", "Existing personality for netperssvcmap tests"]
        self.noouttest(command)
        self.verifycatforpersonality("aquilon", "eaitools")

    def testverifyutpersonalitynothreshold(self):
        user = self.config.get("unittest", "user")
        command = ["show_personality", "--sandbox=%s/changetest1" % user,
                   "--archetype=aquilon", "--personality=utpersonality/dev"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: None", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)
        self.matchoutput(out, "GRN: %s" % GRN, command)

    def testverifyshowpersonalityallnothreshold(self):
        user = self.config.get("unittest", "user")
        command = "show_personality --all --sandbox %s/changetest1" % user
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
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
                   "--archetype=aquilon", "--personality=utpersonality/dev"]
        out = self.commandtest(command)
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: 50", command)
        self.matchclean(out, "Personality: inventory Archetype: aquilon",
                        command)
        self.matchclean(out,
                        "Template: aquilon/personality/inventory/config.tpl",
                        command)

    def testverifyshowpersonalityallthreshold(self):
        command = "show_personality --all --domain unittest"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
                         command)
        self.matchoutput(out, "Threshold: 50", command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)

    def testverifyshowpersonalityall(self):
        command = "show_personality --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
                         command)
        self.matchoutput(out, "Personality: generic Archetype: aurora",
                         command)
        self.matchoutput(out,
                         "Template: aurora/personality/generic/config.tpl",
                         command)
        self.matchclean(out, "Threshold:", command)

    def testverifyshowutpersonalityproto(self):
        command = ["show_personality", "--archetype=aquilon",
                   "--personality=utpersonality/dev", "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality/dev")
        self.failUnlessEqual(personality.threshold, -1)
        self.failUnlessEqual(personality.config_override, True)
        self.failUnlessEqual(personality.cluster_required, False)
        self.failUnlessEqual(personality.comments, "Some personality comments")
        self.failUnlessEqual(personality.owner_eonid, 2)
        self.failUnlessEqual(personality.host_environment, "dev")

    def testverifyshowpersonalityallproto(self):
        command = "show_personality --all --format=proto"
        out = self.commandtest(command.split(" "))
        pl = self.parse_personality_msg(out)
        archetypes = {}
        found_threshold = False
        for personality in pl.personalities:
            archetype = personality.archetype.name
            if archetype in archetypes:
                archetypes[archetype][personality.name] = personality
            else:
                archetypes[archetype] = {personality.name: personality}
            if personality.threshold >= 0:
                found_threshold = True
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality/dev" in archetypes["aquilon"],
                        "No aquilon/utpersonality/dev in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality/dev"].threshold,
                             -1,
                             "Got threshold %s for aquilon/utpersonality/dev" %
                             archetypes["aquilon"]["utpersonality/dev"].threshold)
        self.failIf(found_threshold,
                    "Found a threshold defined when none expected.")

    def testverifyshowutpersonalityprotonothreshold(self):
        user = self.config.get("unittest", "user")
        command = ["show_personality", "--sandbox=%s/changetest1" % user,
                   "--archetype=aquilon", "--personality=utpersonality/dev",
                   "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality/dev")
        self.failUnlessEqual(personality.threshold, -1)
        self.failUnlessEqual(personality.config_override, True)
        self.failUnlessEqual(personality.cluster_required, False)
        self.failUnlessEqual(personality.comments, "Some personality comments")
        self.failUnlessEqual(personality.owner_eonid, 2)

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
                archetypes[archetype] = {personality.name: personality}
            if personality.threshold >= 0:
                found_threshold = True
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality/dev" in archetypes["aquilon"],
                        "No aquilon/utpersonality/dev in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality/dev"].threshold,
                             -1,
                             "Got threshold %s for aquilon/utpersonality/dev" %
                             archetypes["aquilon"]["utpersonality/dev"].threshold)
        self.failUnless(found_threshold,
                        "No thresholds defined in sandbox changetest1.")

    def testverifyshowutpersonalityprotothreshold(self):
        command = ["show_personality", "--domain=unittest",
                   "--archetype=aquilon", "--personality=utpersonality/dev",
                   "--format=proto"]
        out = self.commandtest(command)
        pl = self.parse_personality_msg(out, 1)
        personality = pl.personalities[0]
        self.failUnlessEqual(personality.archetype.name, "aquilon")
        self.failUnlessEqual(personality.name, "utpersonality/dev")
        self.failUnlessEqual(personality.threshold, 50)
        self.failUnlessEqual(personality.config_override, True)
        self.failUnlessEqual(personality.cluster_required, False)
        self.failUnlessEqual(personality.comments, "Some personality comments")
        self.failUnlessEqual(personality.owner_eonid, 2)

    def testverifyshowpersonalityallprotothreshold(self):
        command = "show_personality --all --domain unittest --format=proto"
        out = self.commandtest(command.split(" "))
        pl = self.parse_personality_msg(out)
        archetypes = {}
        for personality in pl.personalities:
            archetype = personality.archetype.name
            if archetype in archetypes:
                archetypes[archetype][personality.name] = personality
            else:
                archetypes[archetype] = {personality.name: personality}
        self.failUnless("aquilon" in archetypes,
                        "No personality with archetype aquilon in list.")
        self.failUnless("utpersonality/dev" in archetypes["aquilon"],
                        "No aquilon/utpersonality/dev in personality list.")
        self.failUnless("aurora" in archetypes,
                        "No personality with archetype aurora")
        self.failUnless("generic" in archetypes["aurora"],
                        "No aquilon/generic in personality list.")
        self.failUnlessEqual(archetypes["aquilon"]["utpersonality/dev"].threshold,
                             50,
                             "Got threshold %s for aquilon/utpersonality/dev" %
                             archetypes["aquilon"]["utpersonality/dev"].threshold)

    def testverifyshowpersonalityarchetype(self):
        command = "show_personality --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Personality: utpersonality/dev Archetype: aquilon",
                         command)
        self.matchoutput(out,
                         "Template: "
                         "aquilon/personality/utpersonality/dev/config.tpl",
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
        command = "show_personality --archetype archetype-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowarchetypeunavailable2(self):
        command = ["show_personality",
                   "--archetype", "archetype-does-not-exist",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Archetype archetype-does-not-exist", command)

    def testshowpersonalityunavailable(self):
        command = ["show_personality", "--archetype", "aquilon",
                   "--personality", "personality-does-not-exist"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Personality personality-does-not-exist, "
                         "archetype aquilon not found.", command)

    def testshowpersonalityunavailable2(self):
        command = ["show_personality",
                   "--personality", "personality-does-not-exist"]
        self.noouttest(command)

    def testshowpersonalityname(self):
        command = "show_personality --personality generic"
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
        command = "add_personality --personality desktop --archetype windows --eon_id=2 --host_environment=legacy"
        self.noouttest(command.split(" "))
        self.verifycatforpersonality("windows", "desktop")

    def testverifyaddwindowsdesktop(self):
        command = "show_personality --personality desktop --archetype windows"
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
                   "--host_environment=legacy",
                   "--archetype=aquilon", "--eon_id=2"]
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
                   "--host_environment=legacy",
                   "--archetype=aquilon", "--eon_id=2"]
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
                   "--host_environment=dev",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality name 'this is a bad; name' is "
                         "not valid", command)

    def testaddinvalidenvironment(self):
        command = ["add_personality", "--personality", "invalidenvironment",
                   "--host_environment", "badenv",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Unknown environment value 'badenv'. The valid"
                              " values are: dev, infra, legacy, prod, qa, uat",
                         command)

    def testaddnotmatchingnameenv01(self):
        command = ["add_personality", "--personality", "test/dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2" ]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test/dev' "
                              "does not match the host environment 'qa'",
                         command)

    def testaddnotmatchingnameenv02(self):
        command = ["add_personality", "--personality", "test-dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2" ]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-dev' "
                              "does not match the host environment 'qa'",
                         command)

    def testaddselectivenamematchenv03(self):
        command = ["add_personality", "--personality", "ec-infra-auth",
                   "--host_environment", "infra",
                   "--archetype", "vmhost", "--eon_id=2" ]
        out = self.successtest(command)

    def testaddnotmatchingnameenv04(self):
        command = ["add_personality", "--personality", "test-qa-dev",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2" ]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-qa-dev' "
                              "does not match the host environment 'qa'",
                         command)

    def testaddnotmatchingnameenv05(self):
        command = ["add_personality", "--personality", "test-qa-DEV",
                   "--host_environment", "qa",
                   "--archetype", "aquilon", "--eon_id=2" ]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Environment value in personality name 'test-qa-DEV' "
                              "does not match the host environment 'qa'",
                         command)

    def testaddduplicate(self):
        command = ["add_personality", "--personality", "inventory",
                   "--host_environment=legacy",
                   "--archetype", "aquilon", "--eon_id=2"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Personality inventory, archetype aquilon "
                         "already exists.", command)

    def testaddesxserver(self):
        command = ["add_personality", "--cluster_required", "--eon_id=2",
                   "--host_environment=legacy",
                   "--personality=esx_server", "--archetype=vmhost"]
        self.noouttest(command)
        self.verifycatforpersonality("vmhost", "esx_server")
        command = ["show_personality", "--personality=esx_server",
                   "--archetype=vmhost"]
        out = self.commandtest(command)
        self.matchoutput(out, "Requires clustered hosts", command)

        command = ["add_personality", "--eon_id=2", "--host_environment=legacy",
                   "--personality=esx_server", "--archetype=esx_cluster"]
        self.noouttest(command)
        self.verifycatforpersonality("esx_cluster", "esx_server")

    def testaddv1personalities(self):
        command = ["add_personality", "--cluster_required", "--host_environment=prod",
                   "--personality=vulcan-1g-desktop-prod", "--archetype=vmhost", "--eon_id=2"]
        self.noouttest(command)
        command = ["add_personality", "--host_environment=prod",
                   "--personality=vulcan-1g-desktop-prod", "--archetype=esx_cluster", "--eon_id=2"]
        self.noouttest(command)
        command = ["add_personality", "--host_environment=legacy",
                   "--personality=metacluster", "--archetype=metacluster", "--eon_id=2"]
        self.noouttest(command)

    def testaddv2personalities(self):
        command = ["add_personality", "--cluster_required", "--host_environment=legacy",
                   "--personality=vulcan2-10g-test", "--archetype=vmhost", "--eon_id=2"]
        self.noouttest(command)
        command = ["add_personality", "--host_environment=legacy",
                   "--personality=vulcan2-10g-test", "--archetype=esx_cluster", "--eon_id=2"]
        self.noouttest(command)
        command = ["add_personality", "--host_environment=legacy",
                   "--personality=vulcan2-test", "--archetype=metacluster", "--eon_id=2"]
        self.noouttest(command)
        self.verifycatforpersonality("esx_cluster", "vulcan2-10g-test")

    def testaddesxstandalone(self):
        command = ["add_personality", "--personality=esx_standalone",
                   "--host_environment=legacy",
                   "--archetype=vmhost", "--eon_id=2"]
        self.noouttest(command)
        self.verifycatforpersonality("vmhost", "esx_standalone")
        command = ["show_personality", "--personality=esx_standalone",
                   "--archetype=vmhost"]
        out = self.commandtest(command)
        self.matchclean(out, "Requires clustered hosts", command)

    def testaddgridpersonality(self):
        command = ["add_personality", "--eon_id=2", "--host_environment=legacy",
                   "--personality=hadoop", "--archetype=gridcluster"]
        self.noouttest(command)
        self.verifycatforpersonality("gridcluster", "hadoop")

    def testaddhapersonality(self):
        command = ["add_personality", "--eon_id=2", "--host_environment=legacy",
                   "--personality=vcs-msvcs", "--archetype=hacluster"]
        self.noouttest(command)
        self.verifycatforpersonality("hacluster", "vcs-msvcs")

    def verifycatforpersonality(self, archetype, personality, config_override=False,
                                host_env='legacy'):
        command = ["cat", "--archetype", archetype, "--personality", personality]
        out = self.commandtest(command)
        self.matchoutput(out, 'variable PERSONALITY = "%s"' % personality,
                         command)
        self.matchoutput(out, '"/system/eon_ids" = push(2);', command)
        self.matchoutput(out, 'include { if_exists("personality/%s/pre_feature") };' %
                         personality, command)
        self.matchoutput(out, "template personality/%s/config;" % personality,
                         command)
        self.matchoutput(out, '"/system/personality/name" = "%s";' % personality,
                         command)
        self.matchoutput(out, '"/system/personality/host_environment" = "%s";' % host_env,
                         command)
        if config_override:
            self.searchoutput(out, r'include { "features/personality/config_override/config" };\s*'
                                   r'include { if_exists\("personality/utpersonality/dev/post_feature"\) };',
                              command)
        else:
            self.matchoutput(out, 'include { if_exists("personality/%s/post_feature") };' %
                             personality, command)
            self.matchclean(out, 'config_override', command)

    def testverifyshowdiff1(self):
        command = ["show_diff", "--personality=utpersonality/dev",
                   "--archetype=aquilon", "--other=generic"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'missing Options in Personality aquilon/generic:\s+ConfigOverride',
                          command)
        self.searchoutput(out,
                          r'missing Grns in Personality aquilon/generic:\s+GRN grn:/ms/ei/aquilon/aqd',
                          command)

    def testverifyshowdiff2(self):
        command = ["show_diff", "--personality=utpersonality/dev",
                   "--archetype=aquilon", "--other=esx_server", "--other_archetype=vmhost"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'missing Options in Personality aquilon/utpersonality/dev:\s+Cluster Required',
                          command)
        self.searchoutput(out,
                          r'matching Options with different values:\s+Environment value=dev, othervalue=legacy',
                          command)
        self.searchoutput(out,
                          r'missing Options in Personality vmhost/esx_server:\s+ConfigOverride',
                          command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddPersonality)
    unittest.TextTestRunner(verbosity=2).run(suite)
