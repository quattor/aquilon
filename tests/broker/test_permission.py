#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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

import unittest
import re
from subprocess import Popen, PIPE

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPermission(TestBrokerCommand):

    def test_000_parse_klist(self):
        """Run klist and stash information."""
        klist = self.config.get('kerberos', 'klist')
        p = Popen([klist], stdout=PIPE, stderr=2)
        (out, err) = p.communicate()
        m = re.search(r'^Default principal:\s+'
                      r'(?P<principal>(?P<user>.*)@(?P<realm>.*?))$',
                      out, re.M)
        self.assertTrue(m,
                        "Could not determine default principal from klist "
                        "output: %s" % out)
        self.config.set('unittest', 'principal', m.group('principal'))
        self.config.set('unittest', 'user', m.group('user'))
        self.config.set('unittest', 'realm', m.group('realm'))

    def testpermissionnobody(self):
        principal = 'testusernobody@' + self.config.get('unittest', 'realm')
        command = ["permission", "--principal", principal,
                   "--role", "nobody", "--createuser",
                   "--comments", "Some user comments"]
        self.noouttest(command)

    def testverifynobody(self):
        principal = 'testusernobody@' + self.config.get('unittest', 'realm')
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "UserPrincipal: %s [role: nobody]" % principal,
                         command)
        self.matchoutput(out, "Comments: Some user comments", command)

    def testverifycsvnocomments(self):
        command = ["show_principal", "--principal=testusernobody@is1.morgan",
                   "--format=csv"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^testusernobody@is1.morgan,nobody$", command)

    def testverifynohostpart(self):
        command = ["permission", "--principal", "testusernobody",
                   "--role", "nobody", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testusernobody' is not valid.",
                         command)

    def testpermissionoperations(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuseroperations@' + realm
        command = ["permission", "--principal", principal, "--role=operations",
                   "--createuser"]
        self.noouttest(command)

    def testverifyoperations(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuseroperations@' + realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "UserPrincipal: %s [role: operations]" % principal,
                         command)

    def testverifycsv(self):
        command = ["show_principal",
                   "--principal=testuseroperations@is1.morgan", "--format=csv"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^testuseroperations@is1.morgan,operations$",
                          command)

    def testpermissionengineering(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserengineering@' + realm
        command = ["permission", "--principal", principal,
                   "--role=engineering", "--createuser"]
        self.noouttest(command)

    def testverifyengineering(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserengineering@' + realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "UserPrincipal: %s [role: engineering]" % principal,
                         command)

    def testpermissionaqd_admin(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuseraqd_admin@' + realm
        command = ["permission", "--principal", principal, "--role=aqd_admin",
                   "--createuser"]
        self.noouttest(command)

    def testverifyaqd_admin(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuseraqd_admin@' + realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "UserPrincipal: %s [role: aqd_admin]" % principal,
                         command)

    def testpromote(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserpromote@' + realm
        command = ["permission", "--principal", principal, "--role=nobody",
                   "--createuser"]
        self.noouttest(command)
        command = ["permission", "--principal", principal,
                   "--role=engineering"]
        self.noouttest(command)

    def testverifypromote(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserpromote@' + realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "UserPrincipal: %s [role: engineering]" % principal,
                         command)

    def testdemote(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserdemote@' + realm
        command = ["permission", "--principal", principal, "--role=operations",
                   "--createuser"]
        self.noouttest(command)
        command = ["permission", "--principal", principal, "--role=nobody"]
        self.noouttest(command)

    def testverifydemote(self):
        realm = self.config.get('unittest', 'realm')
        principal = 'testuserdemote@' + realm
        command = "show principal --principal " + principal
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "UserPrincipal: %s [role: nobody]" % principal,
                         command)

    def testmissinguser(self):
        realm = self.config.get('unittest', 'realm')
        command = ["permission", "--principal", "@" + realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal '@%s' is not valid." % realm,
                         command)

    def testmissingrealm(self):
        command = ["permission", "--principal", "testuser",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testuser' is not valid.",
                         command)

    def testmissinghostname(self):
        realm = self.config.get('unittest', 'realm')
        command = ["permission", "--principal", "host/@%s" % realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No fully qualified name specified.", command)

    def testmissingdomain(self):
        realm = self.config.get('unittest', 'realm')
        command = ["permission", "--principal", "host/no-domain@%s" % realm,
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "FQDN 'no-domain' is not valid, it does not "
                         "contain a domain.",
                         command)

    def testunknownhost(self):
        realm = self.config.get('unittest', 'realm')
        principal = "host/no-such-host.aqd-unittest.ms.com@" + realm
        command = ["permission", "--role", "operations", "--createuser",
                   "--principal", principal]
        out = self.notfoundtest(command)
        # Ideally we would test for a "Host not found", but the DNS domains
        # aren't set up yet.
        self.matchoutput(out,
                         "DNS Domain aqd-unittest.ms.com not found.",
                         command)

    def test_autherror_100(self):
        self.demote_current_user()

    def test_autherror_200(self):
        principal = self.config.get('unittest', 'principal')
        user = self.config.get('unittest', 'user')
        realm = self.config.get('unittest', 'realm')

        command = ["permission", "--role=aqd_admin", "--principal", principal]
        err = self.unauthorizedtest(command, auth=True)
        message = self.config.get("broker", "authorization_error")
        self.matchoutput(err,
                         "Unauthorized access attempt by %s to permission on "
                         "/principal/%s%%40%s/role.  %s" %
                         (principal, user, realm, message),
                         command)

    def test_autherror_900(self):
        self.promote_current_user()


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermission)
    unittest.TextTestRunner(verbosity=2).run(suite)
