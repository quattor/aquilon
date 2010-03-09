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
"""Module for testing the add_network command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.6"))

from brokertest import TestBrokerCommand


class TestAddNetwork(TestBrokerCommand):

    def testaddnetwork(self):
        for network in self.net.all:
            command = ["add_network", "--network=%s" % network.ip,
                       "--ip=%s" % network.ip, "--mask=%s" % network.numhosts,
                       "--building=ut", "--type=%s" % network.nettype]
            self.noouttest(command)

    def testshownetwork(self):
        for network in self.net.all:
            command = "show network --ip %s" % network.ip
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Network: %s" % network.ip, command)
            self.matchoutput(out, "IP: %s" % network.ip, command)
            self.matchoutput(out, "Netmask: %s" % network.netmask, command)
            self.matchoutput(out, "Sysloc: ut.ny.na", command)
            self.matchoutput(out, "Country: us", command)
            self.matchoutput(out, "Side: a", command)
            self.matchoutput(out, "Network Type: %s" % network.nettype,
                             command)
            self.matchoutput(out, "Discoverable: False", command)
            self.matchoutput(out, "Discovered: False", command)

    def testshownetworkbuilding(self):
        command = "show_network --building ut"
        out = self.commandtest(command.split(" "))
        for network in self.net.all:
            self.matchoutput(out, str(network.ip), command)

    def testshownetworkcsv(self):
        command = "show_network --building ut --format csv"
        out = self.commandtest(command.split(" "))
        for network in self.net.all:
            self.matchoutput(out, "%s,%s,%s,ut.ny.na,us,a,%s,\n" % (
                network.ip, network.ip, network.netmask, network.nettype),
                command)

    def testshownetworkproto(self):
        command = "show network --building ut --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_netlist_msg(out)

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)

