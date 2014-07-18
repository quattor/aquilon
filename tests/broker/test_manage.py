#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the manage command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand
from broker.personalitytest import PersonalityTestMixin


class TestManage(PersonalityTestMixin, TestBrokerCommand):

    def test_100_manage_unittest02(self):
        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               want_exist=True)
        # we are using --force to bypass checks because the source domain unittest
        # latest commit does not exist in template-king
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
                        "--sandbox", "%s/changetest1" % self.user, "--force"])
        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               want_exist=False)

    def test_101_verify_cleanup(self):
        basedir = self.config.get("broker", "basedir")
        command = [basedir,
                   "-name", "unittest02.one-nyp.ms.com*",
                   "-path", "*/unittest/*"]
        # basedir may contain the string ".../unittest/..."
        out = ["BASEDIR" + name[len(basedir):] for name in
               self.findcommand(command)]
        self.matchclean(" ".join(out), "/unittest/",
                        "find %s" % " ".join(command))

    def test_105_cat_unittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "changetest1";', command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "sandbox";', command)
        self.matchoutput(out,
                         '"/metadata/template/branch/author" = "%s";' % self.user,
                         command)

    def test_105_show_unittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Sandbox: %s/changetest1" % self.user, command)

    def test_108_manage_unittest02_again(self):
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
                        "--sandbox", "%s/changetest1" % self.user])
        self.verify_buildfiles("unittest", "unittest02.one-nyp.ms.com",
                               want_exist=False)
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "changetest1";', command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "sandbox";', command)
        self.matchoutput(out,
                         '"/metadata/template/branch/author" = "%s";' % self.user,
                         command)

    def test_110_manage_server1(self):
        # we are using --force to bypass checks because the source domain unittest
        # latest commit does not exist in template-king
        self.noouttest(["manage", "--hostname", "server1.aqd-unittest.ms.com",
                        "--domain", "unittest", "--force"])
        command = ["cat", "--hostname", "server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "unittest";', command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "domain";', command)

    def test_115_verify_server1(self):
        command = "show host --hostname server1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: server1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Domain: unittest", command)

    def test_120_manage_unittest00(self):
        self.verify_buildfiles("unittest", "unittest00.one-nyp.ms.com",
                               want_exist=True)
        # we are using --force to bypass checks because the source domain unittest
        # latest commit does not exist in template-king
        self.noouttest(["manage", "--hostname", "unittest00.one-nyp.ms.com",
                        "--sandbox", "%s/changetest2" % self.user, "--force"])
        self.verify_buildfiles("unittest", "unittest00.one-nyp.ms.com",
                               want_exist=False)

    def test_125_verify_unittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Sandbox: %s/changetest2" % self.user, command)

    def test_130_manage_utecl1(self):
        # To compile, this needs templates from the unittest domain.
        # This test takes advantage of the fact that those templates
        # started in the utsandbox sandbox.
        self.verify_buildfiles("unittest", "clusters/utecl1", want_exist=True)
        command = ["search_host", "--cluster", "utecl1"]
        hosts = self.commandtest(command).splitlines()
        self.failUnless(hosts, "No hosts in cluster utecl1, bad test.")
        for host in hosts:
            self.verify_buildfiles("unittest", host, want_exist=True)

        # we want to manage utecl1, but have to do it at metacluster level.
        # we are using --force to bypass checks because the source domain unittest
        # latest commit does not exist in template-king
        command = ["manage", "--cluster", "utmc1",
                   "--sandbox", "%s/utsandbox" % self.user, "--force"]
        self.noouttest(command)
        self.verify_buildfiles("unittest", "clusters/utecl1", want_exist=False)
        for host in hosts:
            self.verify_buildfiles("unittest", host, want_exist=False)
        command = ["compile", "--sandbox=%s/utsandbox" % self.user]
        self.successtest(command)
        self.verify_buildfiles("utsandbox", "clusters/utecl1",
                               want_exist=True)
        for host in hosts:
            self.verify_buildfiles("utsandbox", host, want_exist=True)

    def test_135_verify_utecl1(self):
        command = ["show_esx_cluster", "--cluster=utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Sandbox: %s/utsandbox" % self.user, command)

        command = ["cat", "--cluster", "utecl1"]
        out = self.commandtest(command)
        self.matchoutput(out, '"/metadata/template/branch/name" = "utsandbox";', command)
        self.matchoutput(out, '"/metadata/template/branch/type" = "sandbox";', command)
        self.matchoutput(out,
                         '"/metadata/template/branch/author" = "%s";' % self.user,
                         command)

        command = ["search_host", "--cluster=utecl1"]
        out = self.commandtest(command)
        members = sorted(out.splitlines())
        self.failUnless(members, "No hosts in output of %s." % command)

        command = ["search_host", "--cluster=utecl1",
                   "--sandbox=%s/utsandbox" % self.user]
        out = self.commandtest(command)
        aligned = sorted(out.splitlines())
        self.failUnlessEqual(members, aligned,
                             "Not all utecl1 cluster members (%s) are in "
                             "sandbox utsandbox (%s)." % (members, aligned))

    def test_140_xml_profiles(self):
        self.noouttest(["manage", "--domain", "unittest-xml", "--force",
                        "--hostname", "unittest20.aqd-unittest.ms.com"])
        self.successtest(["compile", "--hostname", "unittest20.aqd-unittest.ms.com"])
        self.verify_buildfiles("unittest-xml", "unittest20.aqd-unittest.ms.com",
                               xml=True, json=False)

    def test_145_json_profiles(self):
        self.noouttest(["manage", "--domain", "unittest-json", "--force",
                        "--hostname", "unittest20.aqd-unittest.ms.com"])
        self.successtest(["compile", "--hostname", "unittest20.aqd-unittest.ms.com"])
        self.verify_buildfiles("unittest-json", "unittest20.aqd-unittest.ms.com",
                               xml=False, json=True)

    def test_150_setup_featuretest(self):
        self.create_personality("aquilon", "featuretest")
        self.noouttest(["add_feature", "--feature", "notemplate",
                        "--type", "host"])
        self.noouttest(["manage", "--hostname", "aquilon68.aqd-unittest.ms.com",
                        "--domain", "unittest", "--force"])
        self.statustest(["reconfigure", "--hostname", "aquilon68.aqd-unittest.ms.com",
                         "--personality", "featuretest"])

    def test_151_bind_no_template(self):
        command = ["bind_feature", "--feature", "notemplate",
                   "--personality", "featuretest"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature notemplate does not have templates "
                         "present in domain unittest for archetype aquilon.",
                         command)

    def test_152_move_aquilon68_to_sandbox(self):
        self.noouttest(["manage", "--hostname", "aquilon68.aqd-unittest.ms.com",
                        "--sandbox", "%s/utsandbox" % self.user, "--force"])

    def test_153_bind_feature(self):
        # The only host in the personality is in a sandbox, so the bind should
        # succeed
        command = ["bind_feature", "--feature", "notemplate",
                   "--personality", "featuretest"]
        err = self.statustest(command)
        self.matchoutput(err, "Flushed 1/1 templates.", command)

    def test_154_manage_notemplate(self):
        command = ["manage", "--hostname", "aquilon68.aqd-unittest.ms.com",
                   "--domain", "unittest"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Host Feature notemplate does not have templates "
                         "present in domain unittest for archetype aquilon.",
                         command)

    def test_155_manage_notemplate_force(self):
        # --force means you know what you're doing...
        self.noouttest(["manage", "--hostname", "aquilon68.aqd-unittest.ms.com",
                        "--domain", "unittest", "--force"])

    def test_159_cleanup_featuretest(self):
        self.noouttest(["manage", "--hostname", "aquilon68.aqd-unittest.ms.com",
                        "--sandbox", "%s/utsandbox" % self.user, "--force"])
        self.statustest(["reconfigure", "--hostname", "aquilon68.aqd-unittest.ms.com",
                         "--personality", "inventory"])
        self.statustest(["unbind_feature", "--feature", "notemplate",
                         "--personality", "featuretest"])
        self.noouttest(["del_feature", "--feature", "notemplate", "--type", "host"])
        self.noouttest(["del_personality", "--personality", "featuretest",
                        "--archetype", "aquilon"])

    def test_160_add_othersandbox(self):
        # We can't run "aq get" in the name of otheruser, so we have to create
        # the sandbox manually
        kingdir = self.config.get("broker", "kingdir")
        self.gitcommand(["branch", "othersandbox", "unittest"], cwd=kingdir)
        dst_dir = os.path.join(self.sandboxdir, "othersandbox")
        self.gitcommand(["clone", kingdir, dst_dir, "--branch", "othersandbox"])

    def test_161_manage_host(self):
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
                        "--sandbox", "otheruser/othersandbox", "--force"])

    def test_162_del_otheruser(self):
        self.noouttest(["del_user", "--username", "otheruser"])

    def test_163_verify_host(self):
        command = ["show_host", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Sandbox: othersandbox [orphaned]", command)

    def test_164_try_compile(self):
        command = ["compile", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.internalerrortest(command)
        self.matchoutput(out,
                         "No author information provided for sandbox "
                         "othersandbox. If the sandbox belonged to an user "
                         "that got deleted, then all hosts/clusters must be "
                         "moved to a sandbox owned by an existing user.",
                         command)

    def test_165_update_personality(self):
        # Any command is good that tries to re-write the host plenary without
        # compiling it
        command = ["rebind_client", "--service", "aqd", "--instance", "ny-prod",
                   "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.statustest(command)
        self.matchoutput(out, "Warning: Host unittest02.one-nyp.ms.com "
                         "is missing sandbox author information.", command)

    def test_169_manage_back(self):
        self.noouttest(["manage", "--hostname", "unittest02.one-nyp.ms.com",
                        "--sandbox", "%s/changetest1" % self.user, "--force"])

    def test_200_nomanage_host(self):
        command = ["manage", "--hostname", "unittest02.one-nyp.ms.com",
                   "--domain", "nomanage"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Managing objects to domain nomanage is not allowed.",
                         command)

    def test_200_nomanage_cluster(self):
        command = ["manage", "--cluster", "utecl1", "--domain", "nomanage"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Managing objects to domain nomanage is not allowed.",
                         command)

    def test_200_manage_cluster_member(self):
        command = ["manage", "--hostname", "evh1.aqd-unittest.ms.com",
                   "--sandbox", "%s/changetest1" % self.user]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cluster nodes must be managed at the cluster level",
                         command)

    def test_200_manage_metacluster_member(self):
        # we are using --force to bypass checks because the source domain unittest
        # latest commit does not exist in template-king
        command = ["manage", "--cluster", "utecl1",
                   "--sandbox", "%s/utsandbox" % self.user, "--force"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "utecl1 is member of metacluster utmc1, it must be "
                         "managed at metacluster level.", command)

    def test_200_bad_cluster(self):
        command = ["manage", "--cluster", "cluster-does-not-exist",
                   "--sandbox", "%s/changetest1" % self.user]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Cluster cluster-does-not-exist not found",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestManage)
    unittest.TextTestRunner(verbosity=2).run(suite)
