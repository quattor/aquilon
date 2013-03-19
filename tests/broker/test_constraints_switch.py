#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Module for testing constraints in commands involving switches."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSwitchConstraints(TestBrokerCommand):

    def testdelmachineastor_switch(self):
        # Deprecated usage.
        command = "del switch --switch ut3c5n10"
        self.badrequesttest(command.split(" "))

    def testverifydelmachineastor_switchfailed(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c5n10", command)

    # This test doesn't make sense right now.
    #def testdeltor_switchasmachine(self):
    #    command = "del machine --machine ut3gd1r01.aqd-unittest.ms.com"
    #    self.badrequesttest(command.split(" "))

    def testverifydeltor_switchasmachinefailed(self):
        # Deprecated usage.
        command = "show switch --switch ut3gd1r01.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Switch: ut3gd1r01", command)

    # Testing that del switch does not delete a blade....
    def testrejectut3c1n3(self):
        # Deprecated usage.
        self.badrequesttest(["del", "switch", "--switch", "ut3c1n3"])

    def testverifyrejectut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Blade: ut3c1n3", command)

    def testdelprimaryinterface(self):
        command = ["del", "interface", "--interface", "xge49",
                   "--switch", "ut3gd1r04.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "holds the primary address", command)

    def testprimaryalias(self):
        command = ["add", "switch", "--switch", "alias2host.aqd-unittest.ms.com",
                   "--type", "misc", "--rack", "ut3", "--model", "uttorswitch",
                   "--ip", self.net.unknown[0].usable[-1]]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Alias alias2host.aqd-unittest.ms.com cannot be "
                         "used for address assignment.", command)

    def testprimarybadip(self):
        good_ip = self.net.unknown[0].usable[13]
        bad_ip = self.net.unknown[0].usable[14]
        command = ["add", "switch", "--switch", "arecord13.aqd-unittest.ms.com",
                   "--type", "misc", "--rack", "ut3", "--model", "uttorswitch",
                   "--ip", bad_ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by DNS record "
                         "arecord14.aqd-unittest.ms.com." % bad_ip,
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSwitchConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
