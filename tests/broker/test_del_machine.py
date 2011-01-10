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
"""Module for testing the del machine command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelMachine(TestBrokerCommand):

    def testdelut3c5n10(self):
        command = "del machine --machine ut3c5n10"
        self.noouttest(command.split(" "))

    def testverifydelut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n3(self):
        command = "del machine --machine ut3c1n3"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n4(self):
        command = "del machine --machine ut3c1n4"
        self.noouttest(command.split(" "))

    def testverifydelut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        self.notfoundtest(command.split(" "))

    def testdelut3c1n8(self):
        command = "del machine --machine ut3c1n8"
        self.noouttest(command.split(" "))

    def testdelut3c1n9(self):
        command = "del machine --machine ut3c1n9"
        self.noouttest(command.split(" "))

    def testdelut3s01p1(self):
        command = "del machine --machine ut3s01p1"
        self.noouttest(command.split(" "))

    def testverifydelut3s01p1(self):
        command = "show machine --machine ut3s01p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p1(self):
        command = "del machine --machine ut8s02p1"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p1(self):
        command = "show machine --machine ut8s02p1"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p2(self):
        command = "del machine --machine ut8s02p2"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p2(self):
        command = "show machine --machine ut8s02p2"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p3(self):
        command = "del machine --machine ut8s02p3"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p3(self):
        command = "show machine --machine ut8s02p3"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p4(self):
        command = "del machine --machine ut8s02p4"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p4(self):
        command = "show machine --machine ut8s02p4"
        self.notfoundtest(command.split(" "))

    def testdelut8s02p5(self):
        command = "del machine --machine ut8s02p5"
        self.noouttest(command.split(" "))

    def testverifydelut8s02p5(self):
        command = "show machine --machine ut8s02p5"
        self.notfoundtest(command.split(" "))

    def testdelhprack(self):
        for i in range(51, 100):
            port = i - 50
            command = "del machine --machine ut9s03p%d" % port
            self.noouttest(command.split(" "))

    def testverifydelhprack(self):
        for i in range(51, 100):
            port = i - 50
            command = "show machine --machine ut9s03p%d" % port
            self.notfoundtest(command.split(" "))

    def testdelverarirack(self):
        for i in range(101, 150):
            port = i - 100
            command = "del machine --machine ut10s04p%d" % port
            self.noouttest(command.split(" "))

    def testverifydelverarirack(self):
        for i in range(101, 150):
            port = i - 100
            command = "show machine --machine ut10s04p%d" % port
            self.notfoundtest(command.split(" "))

    def testdel10gigracks(self):
        for port in range(1, 13):
            command = "del machine --machine ut11s01p%d" % port
            self.noouttest(command.split(" "))
            command = "del machine --machine ut12s02p%d" % port
            self.noouttest(command.split(" "))

    def testdelharacks(self):
        # Machines for metacluster high availability testing
        for port in range(1, 25):
            for rack in ["ut13", "np13"]:
                machine = "%ss03p%d" % (rack, port)
                self.noouttest(["del_machine", "--machine", machine])

    # FIXME: Add a test for deleting a machine with only auxiliaries.

    def testdelut3c5n2(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n2"])

    def testdelut3c5n3(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n3"])

    def testdelut3c5n4(self):
        self.noouttest(["del", "machine", "--machine", "ut3c5n4"])

    def testdeljack(self):
        self.noouttest(["del", "machine", "--machine", "jack"])


if __name__=='__main__':
    import aquilon.aqdb.depends
    import nose
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMachine)

    #unittest.TextTestRunner(verbosity=2).run(suite)
    nose.runmodule()
