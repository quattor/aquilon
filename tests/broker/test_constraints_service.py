#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2012  Contributor
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
"""Module for testing constraints in commands involving domain."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestServiceConstraints(TestBrokerCommand):

    def testdelrequiredservicepersonalitymissing(self):
        command = ["del_required_service", "--service=ntp",
                   "--archetype=windows", "--personality=desktop"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Service ntp required for archetype windows, "
                         "personality desktop not found.", command)

    def testdelservicewithinstances(self):
        command = "del service --service unmapped"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service unmapped still has instances defined "
                         "and cannot be deleted.", command)

    def testdelarchetyperequiredservice(self):
        command = "del service --service aqd"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd is still required by the following "
                         "archetypes: aquilon.", command)

    def testdelpersonalityrequiredservice(self):
        command = "del service --service chooser1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service chooser1 is still required by the "
                         "following personalities: unixeng-test (aquilon).",
                         command)

    def testverifydelservicewithinstances(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd", command)

    def testdelserviceinstancewithservers(self):
        command = "del service --service aqd --instance ny-prod"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd, instance ny-prod is still being "
                         "provided by servers", command)

    def testverifydelserviceinstancewithservers(self):
        command = "show service --service aqd --instance ny-prod"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def testdelserviceinstancewithclients(self):
        command = "del service --service utsvc --instance utsi1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service utsvc, instance utsi1 still has "
                         "clients and cannot be deleted", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestServiceConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
