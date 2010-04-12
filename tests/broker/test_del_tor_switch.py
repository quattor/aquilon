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
"""Module for testing the del tor_switch command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestDelTorSwitch(TestBrokerCommand):

    def testdelut3gd1r01(self):
        command = "del tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut3gd1r01(self):
        command = "show tor_switch --tor_switch ut3gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp997gd1r04(self):
        command = "del tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp997gd1r04(self):
        command = "show tor_switch --tor_switch np997gd1r04.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp998gd1r01(self):
        command = "del tor_switch --tor_switch np998gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp998gd1r01(self):
        command = "show tor_switch --tor_switch np998gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp998gd1r02(self):
        command = "del tor_switch --tor_switch np998gd1r02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testdelnp999gd1r01(self):
        command = "del tor_switch --tor_switch np999gd1r01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp999gd1r01(self):
        command = "show tor_switch --tor_switch np999gd1r01.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp06bals03(self):
        command = "del tor_switch --tor_switch np06bals03.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp06bals03(self):
        command = "show tor_switch --tor_switch np06bals03.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelnp06fals01(self):
        command = "del tor_switch --tor_switch np06fals01.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelnp06bals03(self):
        command = "show tor_switch --tor_switch np06fals01.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s02(self):
        command = "del tor_switch --tor_switch ut01ga1s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut01ga1s02(self):
        command = "show tor_switch --tor_switch ut01ga1s02.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s03(self):
        command = "del tor_switch --tor_switch ut01ga1s03.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut01ga1s03(self):
        command = "show tor_switch --tor_switch ut01ga1s03.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga1s04(self):
        command = "del tor_switch --tor_switch ut01ga1s04.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testverifydelut01ga1s04(self):
        command = "show tor_switch --tor_switch ut01ga1s04.aqd-unittest.ms.com"
        self.notfoundtest(command.split(" "))

    def testdelut01ga2s01(self):
        command = "del tor_switch --tor_switch ut01ga2s01.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))

    def testdelut01ga2s02(self):
        command = "del tor_switch --tor_switch ut01ga2s02.aqd-unittest.ms.com"
        self.noouttest(command.split(" "))


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelTorSwitch)
    unittest.TextTestRunner(verbosity=2).run(suite)

