#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Module for testing the add service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestAddService(TestBrokerCommand):

    def testaddafsinstance(self):
        command = "add service --service afs --instance q.ny.ms.com"
        self.noouttest(command.split(" "))

    def testverifyaddafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)

    def testaddextraafsinstance(self):
        command = "add service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def testverifyaddextraafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)

    def testaddbootserverinstance(self):
        command = "add service --service bootserver --instance np.test"
        self.noouttest(command.split(" "))

    def testverifyaddbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver Instance: np.test", command)

    def testadddnsinstance(self):
        command = "add service --service dns --instance nyinfratest"
        self.noouttest(command.split(" "))

    def testverifyadddnsinstance(self):
        command = "show service --service dns"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: dns Instance: nyinfratest", command)

    def testaddntpinstance(self):
        command = "add service --service ntp --instance pa.ny.na"
        self.noouttest(command.split(" "))

    def testverifyaddntpinstance(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: ntp Instance: pa.ny.na", command)

    def testaddaqdinstance(self):
        command = "add service --service aqd --instance ny-prod"
        self.noouttest(command.split(" "))

    def testverifyaddntpinstance(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: aqd Instance: ny-prod", command)

    def testaddutsi1instance(self):
        command = "add service --service utsvc --instance utsi1"
        self.noouttest(command.split(" "))

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi1';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testcatutsi1default(self):
        command = "cat --service utsvc --instance utsi1 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi1/client/config;",
                         command)
        self.matchoutput(out,
                         "'/system/services/utsvc' = create('servicedata/utsvc/utsi1/config');",
                         command)
        self.matchoutput(out, "include { 'service/utsvc/client/config' };",
                         command)

    def testaddutsi2instance(self):
        command = "add service --service utsvc --instance utsi2"
        self.noouttest(command.split(" "))

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, "include { 'servicedata/utsvc/config' };",
                         command)
        self.matchoutput(out, "'instance' = 'utsi2';", command)
        self.matchoutput(out, "'servers' = list();", command)

    def testcatutsi2default(self):
        command = "cat --service utsvc --instance utsi2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi2/client/config;",
                         command)
        self.matchoutput(out,
                         "'/system/services/utsvc' = create('servicedata/utsvc/utsi2/config');",
                         command)
        self.matchoutput(out, "include { 'service/utsvc/client/config' };",
                         command)

    def testcatutsvc(self):
        command = "cat --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc/config;",
                         command)

    def testcatutsvcdefault(self):
        command = "cat --service utsvc --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/client/config;", command)

    def testverifyaddutsvcinstances(self):
        command = "show service --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def testaddutsvc2(self):
        command = "add service --service utsvc2"
        self.noouttest(command.split(" "))

    def testcatutsvc2(self):
        command = "cat --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc2/config;",
                         command)

    def testcatutsvc2default(self):
        command = "cat --service utsvc2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc2/client/config;",
                         command)

    def testverifyutsvc2(self):
        command = "show service --service utsvc2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: utsvc2", command)

    def testaddchooser1(self):
        command = "add service --service chooser1"
        self.noouttest(command.split(" "))

    def testaddchooser2(self):
        command = "add service --service chooser2"
        self.noouttest(command.split(" "))

    def testaddchooser3(self):
        command = "add service --service chooser3"
        self.noouttest(command.split(" "))

    # Testing server affinity - ut.a will be available to all
    # three of chooser[123], but it will be the only instance
    # (with corresponding server) in common to all three.
    def testaddchooser1uta(self):
        command = "add service --service chooser1 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser1utb(self):
        command = "add service --service chooser1 --instance ut.b"
        self.noouttest(command.split(" "))

    def testaddchooser1utc(self):
        command = "add service --service chooser1 --instance ut.c"
        self.noouttest(command.split(" "))

    # Skipping ut.b for chooser2
    def testaddchooser2uta(self):
        command = "add service --service chooser2 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser2utc(self):
        command = "add service --service chooser2 --instance ut.c"
        self.noouttest(command.split(" "))

    # Skipping ut.c for chooser3
    def testaddchooser3uta(self):
        command = "add service --service chooser3 --instance ut.a"
        self.noouttest(command.split(" "))

    def testaddchooser3utb(self):
        command = "add service --service chooser3 --instance ut.b"
        self.noouttest(command.split(" "))

    def testaddbadservice(self):
        # This service will not have any instances...
        command = "add service --service badservice"
        self.noouttest(command.split(" "))

    def testverifyaddbadservice(self):
        command = "show service --service badservice"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: badservice", command)

    def testaddunmappedservice(self):
        # These service instances will not have any maps...
        command = "add service --service unmapped --instance instance1"
        self.noouttest(command.split(" "))

    def testverifyunmappedservice(self):
        command = "show service --service unmapped"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: unmapped", command)

    def testaddesxlicense(self):
        command = "add service --service esx_license --instance ut.a"
        self.noouttest(command.split(" "))
        command = "add service --service esx_license --instance ut.b"
        self.noouttest(command.split(" "))

    def testverifyesxlicense(self):
        command = "show service --service esx_license"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: esx_license", command)
        self.matchoutput(out, "Service: esx_license Instance: ut.a", command)
        self.matchoutput(out, "Service: esx_license Instance: ut.b", command)

    def testaddesxmanagement(self):
        command = "add service --service esx_management --instance ut.a"
        self.noouttest(command.split(" "))
        command = "add service --service esx_management --instance ut.b"
        self.noouttest(command.split(" "))

    def testverifyesxmanagement(self):
        command = "show service --service esx_management"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: esx_management", command)
        self.matchoutput(out, "Service: esx_management Instance: ut.a",
                         command)
        self.matchoutput(out, "Service: esx_management Instance: ut.b",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddService)
    unittest.TextTestRunner(verbosity=2).run(suite)

