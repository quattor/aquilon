#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Module for testing the permission command.

This is *not* meant to test actual entitlements and permissioning, just
that the 'permission' and 'show principal' commands work as expected.

"""

import unittest
import re
import os
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

    def testautherror(self):
        # Need to demote the current user to test an auth failure.
        principal = self.config.get('unittest', 'principal')
        user = self.config.get('unittest', 'user')
        realm = self.config.get('unittest', 'realm')
        command = ["permission", "--role=nobody", "--principal", principal]
        self.noouttest(command)

        command = ["permission", "--role=aqd_admin", "--principal", principal]
        err = self.unauthorizedtest(command, auth=True)
        message = self.config.get("broker", "authorization_error")
        self.matchoutput(err,
                         "Unauthorized access attempt by %s to permission on "
                         "/principal/%s%%40%s/role.  %s" %
                         (principal, user, realm, message),
                         command)

        # Now fix it.
        srcdir = self.config.get("broker", "srcdir")
        add_admin = os.path.join(srcdir, "tests", "aqdb", "add_admin.py")
        env = os.environ.copy()
        env['AQDCONF'] = self.config.baseconfig
        p = Popen([add_admin], stdout=PIPE, stderr=PIPE, env=env)
        (out, err) = p.communicate()
        self.assertEqual(p.returncode, 0,
                         "Failed to restore admin privs '%s', '%s'." %
                         (out, err))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermission)
    unittest.TextTestRunner(verbosity=2).run(suite)
