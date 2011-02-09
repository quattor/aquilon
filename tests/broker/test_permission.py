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

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestPermission(TestBrokerCommand):

    def testpermissionnobody(self):
        command = ["permission", "--principal", "testusernobody@is1.morgan",
                   "--role", "nobody", "--createuser",
                   "--comments", "Some user comments"]
        self.noouttest(command)

    def testverifynobody(self):
        command = "show principal --principal testusernobody@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testusernobody@is1.morgan [role: nobody]",
                command)
        self.matchoutput(out, "Comments: Some user comments", command)

    def testverifynohostpart(self):
        command = ["permission", "--principal", "testusernobody",
                   "--role", "nobody", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testusernobody' is not valid.",
                         command)

    def testpermissionoperations(self):
        command = "permission --principal testuseroperations@is1.morgan --role operations --createuser"
        self.noouttest(command.split(" "))

    def testverifyoperations(self):
        command = "show principal --principal testuseroperations@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testuseroperations@is1.morgan [role: operations]",
                command)

    def testpermissionengineering(self):
        command = "permission --principal testuserengineering@is1.morgan --role engineering --createuser"
        self.noouttest(command.split(" "))

    def testverifyengineering(self):
        command = "show principal --principal testuserengineering@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testuserengineering@is1.morgan [role: engineering]",
                command)

    def testpermissionaqd_admin(self):
        command = "permission --principal testuseraqd_admin@is1.morgan --role aqd_admin --createuser"
        self.noouttest(command.split(" "))

    def testverifyaqd_admin(self):
        command = "show principal --principal testuseraqd_admin@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testuseraqd_admin@is1.morgan [role: aqd_admin]",
                command)

    def testpromote(self):
        command = "permission --principal testuserpromote@is1.morgan --role nobody --createuser"
        self.noouttest(command.split(" "))
        command = "permission --principal testuserpromote@is1.morgan --role engineering"
        self.noouttest(command.split(" "))

    def testverifypromote(self):
        command = "show principal --principal testuserpromote@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testuserpromote@is1.morgan [role: engineering]",
                command)

    def testdemote(self):
        command = "permission --principal testuserdemote@is1.morgan --role operations --createuser"
        self.noouttest(command.split(" "))
        command = "permission --principal testuserdemote@is1.morgan --role nobody"
        self.noouttest(command.split(" "))

    def testverifydemote(self):
        command = "show principal --principal testuserdemote@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testuserdemote@is1.morgan [role: nobody]",
                command)

    def testmissinguser(self):
        command = ["permission", "--principal", "@is1.morgan",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal '@is1.morgan' is not valid.",
                         command)

    def testmissingrealm(self):
        command = ["permission", "--principal", "testuser",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "User principal 'testuser' is not valid.",
                         command)

    def testmissinghostname(self):
        command = ["permission", "--principal", "host/@is1.morgan",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "No fully qualified name specified.", command)

    def testmissingdomain(self):
        command = ["permission", "--principal", "host/no-domain@is1.morgan",
                   "--role", "operations", "--createuser"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "FQDN 'no-domain' is not valid, it does not "
                         "contain a domain.", command)

    def testunknownhost(self):
        command = ["permission", "--role", "operations", "--createuser",
                   "--principal", "host/no-such-host.aqd-unittest.ms.com@is1.morgan"]
        out = self.notfoundtest(command)
        # Ideally we would test for a "Host not found", but the DNS domains
        # aren't set up yet.
        self.matchoutput(out,
                         "DNS Domain aqd-unittest.ms.com not found.",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermission)
    unittest.TextTestRunner(verbosity=2).run(suite)

