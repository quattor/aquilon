#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the add sandbox command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestAddSandbox(TestBrokerCommand):

    def test_100_default_untrusted(self):
        # When the broker auto-creates a realm, it should be untrusted by
        # default
        command = ["show", "realm", "--realm",
                   self.realm]
        out = self.commandtest(command)
        self.matchoutput(out, "Realm: %s" %
                         self.realm, command)
        self.matchoutput(out, "Trusted: False", command)

    def test_101_add_untrusted(self):
        command = ["add", "sandbox", "--sandbox", "untrusted"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Realm %s is not trusted to handle sandboxes."
                         % self.realm,
                         command)

    def test_102_make_trusted(self):
        command = ["update", "realm", "--trusted",
                   "--realm", self.realm]
        self.noouttest(command)

    def test_103_verify_trust(self):
        command = ["show", "realm", "--realm",
                   self.realm]
        out = self.commandtest(command)
        self.matchoutput(out, "Realm: %s" %
                         self.realm, command)
        self.matchoutput(out, "Trusted: True", command)

    def test_103_flip_untrusted(self):
        command = ["update", "realm", "--untrusted",
                   "--realm", self.realm]
        self.noouttest(command)

        command = ["show", "realm", "--realm",
                   self.realm]
        out = self.commandtest(command)
        self.matchoutput(out, "Trusted: False", command)

        command = ["update", "realm", "--trusted",
                   "--realm", self.realm]
        self.noouttest(command)

    def test_110_addutsandbox(self):
        self.noouttest(["add", "sandbox", "--sandbox", "utsandbox",
                        "--comments", "Sandbox used for aqd unit tests",
                        "--noget", "--start=prod"])
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.failIf(os.path.exists(sandboxdir),
                    "Did not expect directory '%s' to exist" % sandboxdir)

    def test_115_verify_utsandbox(self):
        kingdir = self.config.get("broker", "kingdir")
        (out, err) = self.gitcommand(["show-ref", "--hash", "refs/heads/prod"],
                                     cwd=kingdir)
        head = out.strip()

        command = "show sandbox --sandbox utsandbox"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)
        self.matchoutput(out, "Owner: %s@%s" % (self.user, self.realm), command)
        self.matchoutput(out, "Comments: Sandbox used for aqd unit tests",
                         command)
        self.matchoutput(out, "Base Commit: %s" % head, command)
        self.matchclean(out, "Path", command)

    def test_115_verify_utsandbox_proto(self):
        command = ["show_sandbox", "--sandbox", "utsandbox", "--format", "proto"]
        out = self.commandtest(command)
        domainlist = self.parse_domain_msg(out, expect=1)
        domain = domainlist.domains[0]
        self.assertEqual(domain.name, "utsandbox")
        self.assertEqual(domain.owner, "%s@%s" % (self.user, self.realm))
        self.assertEqual(domain.type, domain.SANDBOX)

    def test_115_verify_utsandbox_realm(self):
        command = "show sandbox --sandbox %s@%s/utsandbox" % (self.user, self.realm)
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)

    def test_115_verify_utsandbox_path(self):
        command = "show sandbox --sandbox %s/utsandbox --pathonly" % self.user
        out = self.commandtest(command.split(" "))
        sandboxdir = os.path.join(self.sandboxdir, "utsandbox")
        self.matchoutput(out, sandboxdir, command)

    def test_115_verify_no_author(self):
        command = "show sandbox --sandbox utsandbox --pathonly"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Must specify sandbox as author/branch "
                         "when using --pathonly",
                         command)

    def test_120_add_changetest1(self):
        command = ["add", "sandbox", "--sandbox", "%s/changetest1" % self.user]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "creating %s" % self.sandboxdir, command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def test_125_verify_changetest1(self):
        sandboxdir = os.path.join(self.sandboxdir, "changetest1")
        command = "show sandbox --sandbox %s/changetest1" % self.user
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest1", command)
        self.matchoutput(out, "Path: %s" % sandboxdir, command)
        self.matchclean(out, "Comments", command)

    def test_130_addchangetest2(self):
        command = ["add", "sandbox", "--sandbox", "changetest2"]
        # Progress report may be displayed on stderr, ignore it
        out, err = self.successtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "changetest2")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def test_135_verify_changetest2(self):
        command = "show sandbox --sandbox changetest2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: changetest2", command)

    def test_140_uppercase1(self):
        # For testing mixed-case add.
        command = ["add", "sandbox", "--sandbox", "CamelCaseTest1"]
        # Progress report may be displayed on stderr, ignore it
        out, err = self.successtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def test_150_uppercase2(self):
        # For testing deletion of a sandbox added with mixed case.
        command = ["add", "sandbox", "--sandbox", "CamelCaseTest2"]
        # Progress report may be displayed on stderr, ignore it
        out, err = self.successtest(command)
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest2")
        self.matchoutput(out, "Created sandbox: %s" % sandboxdir, command)
        self.failUnless(os.path.exists(sandboxdir),
                        "Expected directory '%s' to exist" % sandboxdir)

    def test_160_verify_lower_branchname(self):
        command = ['branch', '-r']
        sandboxdir = os.path.join(self.sandboxdir, "camelcasetest1")
        (out, err) = self.gitcommand(command, cwd=sandboxdir)
        self.matchoutput(out, "origin/camelcasetest1", command)

    def test_160_verify_show_mixedcase(self):
        command = "show sandbox --sandbox CamelCaseTest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: camelcasetest1", command)

    def test_160_verify_show_lowercase(self):
        command = "show sandbox --sandbox camelcasetest1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: camelcasetest1", command)

    def test_170_show_all(self):
        command = "show sandbox --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Sandbox: utsandbox", command)
        self.matchoutput(out, "Sandbox: changetest1", command)
        self.matchoutput(out, "Sandbox: changetest2", command)

    def test_170_verify_search(self):
        command = ["search", "sandbox", "--owner", self.user]
        out = self.commandtest(command)
        self.matchoutput(out, "utsandbox", command)

    def test_200_add_baduser(self):
        command = ["add", "sandbox",
                   "--sandbox", "cdb@example.realm/badbranch"]
        err = self.badrequesttest(command)
        self.matchoutput(err,
                         "User '%s@%s' cannot add or get a sandbox on "
                         "behalf of 'cdb@example.realm'." % (self.user, self.realm),
                         command)

    def test_200_fail_invalid(self):
        command = "add sandbox --sandbox bad:characters!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'bad:characters!' is not a valid value for "
                         "--sandbox.", command)

    def test_200_slash_in_userid(self):
        command = "add sandbox --sandbox user1/test/nevermade"
        err = self.notfoundtest(command.split(" "))
        self.matchoutput(err, "User 'user1/test' not found.", command)

    def test_200_add_existing_path(self):
        sandboxdir = os.path.join(self.sandboxdir, "existingsand")
        os.makedirs(sandboxdir)
        command = ["add", "sandbox", "--sandbox", "existingsand"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Sandbox directory %s already exists; "
                         "cannot create branch." % sandboxdir, command)
        os.removedirs(sandboxdir)

    def test_200_bad_git_branchname(self):
        command = ["add_sandbox", "--sandbox", "foobar."]
        out = self.badrequesttest(command)
        self.matchoutput(out, "'foobar.' is not a valid git branch name.",
                         command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddSandbox)
    unittest.TextTestRunner(verbosity=2).run(suite)
