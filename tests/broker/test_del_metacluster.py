#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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
"""Module for testing the del metacluster command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelMetaCluster(TestBrokerCommand):

    def testdelutmc1(self):
        command = ["del_metacluster", "--metacluster=utmc1"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        self.notfoundtest(command)

    def testdelutmc2(self):
        command = ["del_metacluster", "--metacluster=utmc2"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc2(self):
        command = ["show_metacluster", "--metacluster=utmc2"]
        self.notfoundtest(command)

    def testdelutmc3(self):
        command = ["del_metacluster", "--metacluster=utmc3"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc3(self):
        command = ["show_metacluster", "--metacluster=utmc3"]
        self.notfoundtest(command)

    def testdelutmc4(self):
        command = ["del_metacluster", "--metacluster=utmc4"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc5(self):
        command = ["del_metacluster", "--metacluster=utmc5"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc6(self):
        command = ["del_metacluster", "--metacluster=utmc6"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc7(self):
        command = ["del_metacluster", "--metacluster=utmc7"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutsandbox(self):
        # Test moving machines between metaclusters
        command = ["del_metacluster", "--metacluster=sandboxmc"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelvulcan1(self):
        command = ["del_metacluster", "--metacluster=vulcan1"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifyall(self):
        command = ["show_metacluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Metacluster: utmc", command)

    def testdelnotfound(self):
        command = ["del_metacluster",
                   "--metacluster=metacluster-does-not-exist"]
        self.notfoundtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
