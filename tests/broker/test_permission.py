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
"""Module for testing the permission command.

This is *not* meant to test actual entitlements and permissioning, just
that the 'permission' and 'show principal' commands work as expected.

"""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestPermission(TestBrokerCommand):
    def testpermissionnobody(self):
        principal = 'testusernobody@' + self.realm
        command = ["permission", "--principal", principal,
                   "--role", "nobody", "--createuser",
                   "--comments", "Some user comments"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)

    def testverifynobody(self):
        principal = 'testusernobody@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "User Principal: %s [role: nobody]" % principal,
                         command)
        self.matchoutput(out, "Comments: Some user comments", command)

    def testverifycsvnocomments(self):
        command = ["show_principal", "--principal=testusernobody@%s" % self.realm,
                   "--format=csv"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^testusernobody@%s,nobody$" % self.realm, command)

    def testverifysearchnobody(self):
        principal = 'testusernobody@' + self.realm
        command = ["search_principal", "--role", "nobody", "--fullinfo"]
        out = self.commandtest(command)
        self.matchoutput(out, "User Principal: %s [role: nobody]" % principal,
                         command)
        self.matchoutput(out, "Comments: Some user comments", command)
        self.matchclean(out, "operations", command)
        self.matchclean(out, "engineering", command)

    def testverifynohostpart(self):
        command = ["permission", "--principal", "testusernobody",
                   "--role", "nobody", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testusernobody' is not valid.",
                         command)

    def testpermissionoperations(self):
        principal = 'testuseroperations@' + self.realm
        command = ["permission", "--principal", principal, "--role=operations",
                   "--createuser"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)

    def testverifyoperations(self):
        principal = 'testuseroperations@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "User Principal: %s [role: operations]" % principal,
                         command)

    def testverifycsv(self):
        command = ["show_principal",
                   "--principal=testuseroperations@%s" % self.realm,
                   "--format=csv"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^testuseroperations@%s,operations$" %
                          self.realm, command)

    def testpermissionengineering(self):
        principal = 'testuserengineering@' + self.realm
        command = ["permission", "--principal", principal,
                   "--role=engineering", "--createuser"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)

    def testverifyengineering(self):
        principal = 'testuserengineering@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "User Principal: %s [role: engineering]" % principal,
                         command)

    def testpermissionaqd_admin(self):
        principal = 'testuseraqd_admin@' + self.realm
        command = ["permission", "--principal", principal, "--role=aqd_admin",
                   "--createuser"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)

    def testverifyaqd_admin(self):
        principal = 'testuseraqd_admin@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "User Principal: %s [role: aqd_admin]" % principal,
                         command)

    def testpermissionforeignrealm(self):
        command = ["permission", "--principal", "foreign@foreign",
                   "--role", "operations", "--createuser", "--createrealm"]
        err = self.statustest(command)
        self.matchoutput(err, "User foreign@foreign did not exist, creating.",
                         command)
        self.matchoutput(err, "Realm foreign did not exist, creating.", command)

    def testverifysearchrealm(self):
        command = ["search_principal", "--realm", "foreign"]
        out = self.commandtest(command)
        self.matchoutput(out, "foreign@foreign", command)
        self.matchclean(out, "testengineering", command)
        self.matchclean(out, "testoperations", command)
        self.matchclean(out, "testnobody", command)
        self.matchclean(out, "testtestuseraqd_admin", command)
        self.matchclean(out, '@' + self.realm,
                        command)

    def testpromote(self):
        principal = 'testuserpromote@' + self.realm
        command = ["permission", "--principal", principal, "--role=nobody",
                   "--createuser"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)
        command = ["permission", "--principal", principal,
                   "--role=engineering"]
        self.noouttest(command)

    def testverifypromote(self):
        principal = 'testuserpromote@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "User Principal: %s [role: engineering]" % principal,
                         command)

    def testdemote(self):
        principal = 'testuserdemote@' + self.realm
        command = ["permission", "--principal", principal, "--role=operations",
                   "--createuser"]
        err = self.statustest(command)
        self.matchoutput(err, "User %s did not exist, creating." % principal,
                         command)
        command = ["permission", "--principal", principal, "--role=nobody"]
        self.noouttest(command)

    def testverifydemote(self):
        principal = 'testuserdemote@' + self.realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "User Principal: %s [role: nobody]" % principal,
                         command)

    def testmissinguser(self):
        command = ["permission", "--principal", "@" + self.realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal '@%s' is not valid." % self.realm,
                         command)

    def testmissingrealm(self):
        command = ["permission", "--principal", "testuser",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testuser' is not valid.",
                         command)

    def testmissinghostname(self):
        command = ["permission", "--principal", "host/@%s" % self.realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No fully qualified name specified.", command)

    def testmissingdomain(self):
        command = ["permission", "--principal", "host/no-domain@%s" % self.realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "FQDN 'no-domain' is not valid, it does not "
                         "contain a domain.",
                         command)

    def testunknownhost(self):
        principal = "host/no-such-host.aqd-unittest.ms.com@" + self.realm
        command = ["permission", "--role", "operations", "--createuser",
                   "--principal", principal]
        out = self.notfoundtest(command)
        # Ideally we would test for a "Host not found", but the DNS domains
        # aren't set up yet.
        self.matchoutput(out,
                         "DNS Domain aqd-unittest.ms.com not found.",
                         command)

    def testcreaterealm(self):
        command = ["permission", "--principal", "somebody@realm-does-not-exist",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Could not find realm realm-does-not-exist to create "
                         "principal somebody@realm-does-not-exist, use "
                         "--createrealm to create a new record for the realm.",
                         command)

    def test_autherror_100(self):
        self.demote_current_user()

    def test_autherror_200(self):
        principal = "%s@%s" % (self.user, self.realm)

        command = ["permission", "--role=aqd_admin", "--principal", principal]
        err = self.unauthorizedtest(command, auth=True)
        message = self.config.get("broker", "authorization_error")
        self.matchoutput(err,
                         "Unauthorized access attempt by %s to permission on "
                         "/principal/%s%%40%s/role.  %s" %
                         (principal, self.user, self.realm, message),
                         command)

    def test_autherror_900(self):
        self.promote_current_user()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermission)
    unittest.TextTestRunner(verbosity=2).run(suite)
