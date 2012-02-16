#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2012  Contributor
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
"""Module for testing the del interface command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelInterface(TestBrokerCommand):

    # Not testing del interface for ut3c5n10... testing that those
    # interfaces are removed automatically when the machine is removed.

    def testdelut3c1n3eth0(self):
        self.noouttest(["del", "interface", "--interface", "eth0",
            "--machine", "ut3c1n3"])

    def testdelut3c1n3eth1(self):
        self.noouttest(["del", "interface",
                        "--mac", self.net.unknown[0].usable[3].mac.upper()])

    def testnotamachine(self):
        command = ["del", "interface", "--interface", "xge49",
                   "--machine", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a machine", command)

    def testnotaswitch(self):
        command = ["del", "interface", "--interface", "oa",
                   "--switch", "ut3c5"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a switch", command)

    def testnotachassis(self):
        command = ["del", "interface", "--interface", "eth0",
                   "--chassis", "ut3c5n10"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "but is not a chassis", command)

    def testverifydelut3c1n3interfaces(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "Interface: eth", command)

    def testverifycatut3c1n3interfaces(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "eth0", command)
        self.matchclean(out, "eth1", command)

    def testdelut3gd1r04vlan110(self):
        command = ["del", "interface", "--interface", "vlan110",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        self.noouttest(command)

    def testverifydelut3gd1r04vlan110(self):
        command = ["show", "switch", "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "vlan110", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelInterface)
    unittest.TextTestRunner(verbosity=2).run(suite)

