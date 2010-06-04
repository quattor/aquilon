#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the del service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestDelService(TestBrokerCommand):

    def testdelafsinstance(self):
        command = "del service --service afs --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ny.ms.com", command)

    def testdelextraafsinstance(self):
        command = "del service --service afs --instance q.ln.ms.com"
        self.notfoundtest(command.split(" "))

    def testverifydelextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: afs Instance: q.ln.ms.com", command)

    def testdelbootserverinstance(self):
        command = "del service --service bootserver --instance np.test"
        self.noouttest(command.split(" "))

    def testverifydelbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: bootserver Instance: np.test", command)

    def testdellemoninstance(self):
        command = "del service --service lemon --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifydellemoninstance(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: lemon Instance: ny-prod", command)

    def testdeldnsinstance(self):
        command = "del service --service dns --instance utdnsinstance"
        self.noouttest(command.split(" "))

    def testverifydeldnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: dns Instance: utdnsinstance", command)

    # At this point, pa.ny.na still is still mapped.  del_service
    # should silently remove the mappings.
    def testdelntpinstance(self):
        command = "del service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifydelntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: ntp Instance: pa.ny.na", command)

    def testdelutsi1instance(self):
        command = "del service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testdelutsi2instance(self):
        command = "del service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testverifydelutsvcinstance(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: utsvc Instance: utsi1", command)
        self.matchclean(out, "Service: utsvc Instance: utsi2", command)

    def testdelutsvc2(self):
        command = "del service --service utsvc2"
        self.noouttest(command.split(" "))

    def testverifydelutsvc2(self):
        command = "show service --service utsvc2"
        self.notfoundtest(command.split(" "))

    def testdelunmappedservice(self):
        command = "del service --service unmapped --instance instance1"
        self.noouttest(command.split(" "))

    def testverifydelunmappedservice(self):
        command = "show service --service unmapped"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Service: unmapped Instance: instance1", command)

    def testdelesxmanagement(self):
        command = "del service --service esx_management_server --instance ut.a"
        self.noouttest(command.split(" "))
        command = "del service --service esx_management_server --instance ut.b"
        self.noouttest(command.split(" "))
        command = "del service --service esx_management_server"
        self.noouttest(command.split(" "))

    def testverifydelesxmanagement(self):
        command = "show service --service esx_management_server"
        self.notfoundtest(command.split(" "))

    def testdelvmseasoning(self):
        command = "del service --service vmseasoning --instance salt"
        self.noouttest(command.split(" "))
        command = "del service --service vmseasoning --instance pepper"
        self.noouttest(command.split(" "))
        command = "del service --service vmseasoning"
        self.noouttest(command.split(" "))

    def testverifydelvmseasoning(self):
        command = "show service --service vmseasoning"
        self.notfoundtest(command.split(" "))

    def testdel10gigshares(self):
        for i in range(5, 11):
            self.noouttest(["del_service", "--service=nas_disk_share",
                            "--instance=utecl%d_share" % i])

    def testdelnasshares(self):
        for i in range(1, 10):
            self.noouttest(["del_service", "--service=nas_disk_share",
                            "--instance=test_share_%s" % i])
        self.noouttest(["del_service", "--service=nas_disk_share"])


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelService)
    unittest.TextTestRunner(verbosity=2).run(suite)

