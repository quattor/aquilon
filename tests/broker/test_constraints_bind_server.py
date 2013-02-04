#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing constraints involving the bind server command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestBindServerConstraints(TestBrokerCommand):

    def testrejectdelunittest02(self):
        command = "del host --hostname unittest00.one-nyp.ms.com"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out,
                         "Cannot delete host unittest00.one-nyp.ms.com due "
                         "to the following dependencies:",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com is bound as a server for "
                         "service utsvc instance utsi1",
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com is bound as a server for "
                         "service utsvc instance utsi2",
                         command)

    # Test that unittest00 comes out of utsi1 but stays in utsi2
    def testunbindutsi1unittest00(self):
        self.noouttest(["unbind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    def testverifycatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*"unittest02.one-nyp.ms.com"\s*\);',
                          command)

    def testverifyunbindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest00.one-nyp.ms.com", command)

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*"unittest00.one-nyp.ms.com"\s*\);',
                          command)

    def testverifyutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchclean(out, "Server: unittest02.one-nyp.ms.com", command)

    def testrejectdelserviceinstance(self):
        command = "del service --service utsvc --instance utsi2"
        self.badrequesttest(command.split(" "))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServerConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
