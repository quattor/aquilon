#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013,2014  Contributor
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
"""Module for testing the del domain command."""

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestDelDomain(TestBrokerCommand):

    def test_100_del_utprod(self):
        command = ["del_domain", "--domain=ut-prod"]
        self.successtest(command)
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "ut-prod")))

    def test_101_verify_utprod(self):
        command = ["show_domain", "--domain=ut-prod"]
        self.notfoundtest(command)

    def test_110_del_unittest(self):
        command = ["del_domain", "--domain=unittest"]
        self.successtest(command)
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "unittest")))

    def test_111_verify_unittest(self):
        command = ["show_domain", "--domain=unittest"]
        self.notfoundtest(command)

    def test_120_del_deployable_unarchived(self):
        command = ["del_domain", "--domain=deployable"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Domain deployable is not archived, it cannot "
                         "be deleted.", command)

    def test_121_archive_deployable(self):
        self.noouttest(["update_domain", "--domain", "deployable",
                        "--archived"])

    def test_122_del_archived_no_justification(self):
        command = ["del_domain", "--domain=deployable"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Deleting a domain may lose history, so "
                         "--justification is required.", command)

    def test_123_del_deployable_archived(self):
        command = ["del_domain", "--domain=deployable",
                   "--justification=tcm=123456"]
        self.successtest(command)
        self.failIf(os.path.exists(os.path.join(
            self.config.get("broker", "domainsdir"), "deployable")))

    def test_124_verify_trash(self):
        trash_branch = self.config.get("broker", "trash_branch")
        kingdir = self.config.get("broker", "kingdir")
        command = ["log", "--no-color", "-n", "1", trash_branch]
        out, err = self.gitcommand(command, cwd=kingdir)

        self.matchoutput(out, "Delete archived branch deployable", command)
        self.matchoutput(out, "Justification: tcm=123456", command)

    def test_130_del_unittest_xml(self):
        self.noouttest(["del_domain", "--domain", "unittest-xml"])

    def test_135_del_unittest_json(self):
        self.noouttest(["del_domain", "--domain", "unittest-json"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelDomain)
    unittest.TextTestRunner(verbosity=2).run(suite)
