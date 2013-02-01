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
"""Module for testing the del_network command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelNetwork(TestBrokerCommand):

    def testdelnetwork(self):
        for network in self.net.all:
            command = ["del_network", "--ip=%s" % network.ip]
            self.noouttest(command)

    def testdelauroranetwork(self):
        for ip in ["144.14.174.0", "10.184.155.0"]:
            command = ["del_network", "--ip=%s" % ip]
            self.noouttest(command)

    def testdelnetworkdup(self):
        ip = "192.168.10.0"
        self.noouttest(["del", "network", "--ip", ip])

    def testshownetworkall(self):
        for network in self.net.all:
            command = "show network --ip %s --hosts" % network.ip
            out = self.notfoundtest(command.split(" "))

    def testshownetwork(self):
        command = "show network --building ut"
        out = self.commandtest(command.split(" "))
        # Unfortunately this command prints a header even if the output is
        # otherwise empty. Check for a dot, as that will match any IP addresses,
        # but not the header.
        self.matchclean(out, ".", command)

    def testshownetworkproto(self):
        command = "show network --building ut --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_netlist_msg(out, expect=0)

    def testdelnetworkcards(self):
        command = ["del_network", "--ip=192.168.1.0"]
        self.noouttest(command)

    def test_autherror_100(self):
        self.demote_current_user("operations")

    def test_autherror_200(self):
        # 192.168.2.0 was never actually created, but that check happens
        # after the auth check.
        command = ["del_network", "--ip", "192.168.2.0"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        allowed_roles = self.config.get("site", "change_default_netenv_roles")
        role_list = allowed_roles.strip().split()
        default_ne = self.config.get("site", "default_network_environment")
        self.matchoutput(out,
                         "Only users with %s can modify networks in the %s "
                         "network environment." % (role_list, default_ne),
                         command)

    def test_autherror_300(self):
        command = ["del_network", "--ip", "192.168.3.0",
                   "--network_environment", "cardenv"]
        self.noouttest(command)

    def test_autherror_900(self):
        self.promote_current_user()

    def testdellocalnet(self):
        self.noouttest(["del", "network", "--ip", "127.0.0.0"])

    def testdelexcx(self):
        net = self.net.unknown[0].subnet()[0]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testdelnetsvcmap(self):
        net = self.net.netsvcmap
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def testdelnetperssvcmap(self):
        net = self.net.netperssvcmap
        command = ["del", "network", "--ip", net.ip]
        self.noouttest(command)

    def testdelutcolo(self):
        net = self.net.unknown[1]
        command = ["del", "network", "--ip", net.ip,
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def testverifyexcx(self):
        net = self.net.unknown[0].subnet()[0]
        command = ["search", "network", "--all", "--network_environment", "excx"]
        out = self.commandtest(command)
        self.matchclean(out, "excx-net", command)
        self.matchclean(out, str(net.ip), command)

    def testverifynetsvcmap(self):
        net = self.net.netsvcmap
        command = ["search", "network", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "netsvcmap", command)
        self.matchclean(out, str(net.ip), command)

    def testverifyutcolo(self):
        net = self.net.unknown[1]
        command = ["search", "network", "--all", "--network_environment", "utcolo"]
        out = self.commandtest(command)
        self.matchclean(out, "utcolo-net", command)
        self.matchclean(out, str(net.ip), command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
