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
"""Module for testing the del auxiliary command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelAuxiliary(TestBrokerCommand):

    def testdelunittest00e1(self):
        self.dsdb_expect_delete(self.net.unknown[0].usable[3])
        command = "del auxiliary --auxiliary unittest00-e1.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        self.dsdb_verify()

    def testverifydelunittest00e1(self):
        command = "show auxiliary --auxiliary unittest00-e1.one-nyp.ms.com"
        self.notfoundtest(command.split(" "))

    # FIXME: This is awkward but there is no better user interface yet.
    # test_update_interface assigns an IP to unittest02/eth1, which prevents the
    # machine from being deleted, but the IP cannot be removed if it is not
    # present as a System
    def testdelunittest02e1(self):
        ip = self.net.unknown[0].usable[12]
        self.dsdb_expect_add("unittest02-e1.one-nyp.ms.com", ip)
        command = ["add", "address",
                   "--fqdn", "unittest02-e1.one-nyp.ms.com", "--ip", ip]
        self.noouttest(command)
        self.dsdb_verify()

        self.dsdb_expect_delete(ip)
        command = ["del", "auxiliary", "--auxiliary",
                   "unittest02-e1.one-nyp.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelAuxiliary)
    unittest.TextTestRunner(verbosity=2).run(suite)

