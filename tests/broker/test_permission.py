#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Module for testing the permission command.

This is *not* meant to test actual entitlements and permissioning, just
that the 'permission' and 'show principal' commands work as expected.

"""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestPermission(TestBrokerCommand):

    def testpermissionnobody(self):
        command = "permission --principal testusernobody@is1.morgan --role nobody --createuser"
        self.noouttest(command.split(" "))

    def testverifynobody(self):
        command = "show principal --principal testusernobody@is1.morgan"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                "UserPrincipal: testusernobody@is1.morgan [role: nobody]",
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


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPermission)
    unittest.TextTestRunner(verbosity=2).run(suite)

