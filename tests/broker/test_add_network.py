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
"""Module for testing the add_network command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddNetwork(TestBrokerCommand):

    def testaddnetwork(self):
        for network in self.net.all:
            command = ["add_network", "--network=%s" % network.ip,
                       "--ip=%s" % network.ip,
                       "--netmask=%s" % network.netmask,
                       "--building=ut", "--type=%s" % network.nettype]
            self.noouttest(command)

    def testaddauroranetwork(self):
        self.noouttest(["add_network", "--ip", "144.14.174.0",
                        "--network", "pissp1_aur",
                        "--netmask", "255.255.255.0",
                        "--building", "ut", "--side", "a", "--type", "unknown",
                        "--comments", "Test aurora net"])
        self.noouttest(["add_network", "--ip", "10.184.155.0",
                        "--network", "ny00l4as01_aur",
                        "--netmask", "255.255.255.0",
                        "--building", "np", "--side", "a", "--type", "unknown",
                        "--comments", "Test aurora net"])

    def testaddextranetwork(self):
        # These were previously pulled from DSDB
        self.noouttest(["add_network", "--ip", "172.31.64.64",
                        "--network", "np06bals03_v103",
                        "--netmask", "255.255.255.192",
                        "--building", "np", "--side", "a", "--type", "unknown",
                        "--comments", "Some network comments"])
        self.noouttest(["add_network", "--ip", "172.31.88.0",
                        "--network", "nyp_hpl_2960_verari_mnmt",
                        "--netmask", "255.255.255.192",
                        "--building", "np", "--side", "a", "--type", "unknown"])

    def testaddnetworkdup(self):
        # Old name, new address
        net = self.net.all[0]
        command = ["add", "network", "--network", net.ip,
                   "--ip", "192.168.10.0", "--netmask", "255.255.255.0",
                   "--building", "ut", "--type", net.nettype]
        (out, err) = self.successtest(command)
        self.matchoutput(err, "WARNING: Network name %s is already used for "
                         "address %s." % (str(net.ip), str(net)), command)

    def testaddsubnet(self):
        # Add a subnet of an existing network
        net = self.net.all[0]
        subnet = net.subnet()[1]
        command = ["add", "network", "--network", "subnet-test",
                   "--ip", subnet.ip, "--netmask", subnet.netmask,
                   "--building", "ut", "--type", net.nettype]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address %s is part of existing network "
                         "named %s with address %s." %
                         (str(subnet.ip), str(net.ip), str(net)), command)

    def testaddnetworkofcards(self):
        # An entirely fictitious network
        self.noouttest(["add_network", "--ip", "192.168.1.0",
                        "--network", "cardnetwork",
                        "--netmask", "255.255.255.0",
                        "--building", "cards", "--side", "a",
                        "--type", "unknown",
                        "--comments", "Made-up network"])

    def test_autherror_100(self):
        self.demote_current_user("operations")

    def test_autherror_200(self):
        # Another entirely fictitious network
        command = ["add_network", "--ip", "192.168.2.0",
                   "--network", "cardnetwork2", "--netmask", "255.255.255.0",
                   "--building", "cards", "--side", "a", "--type", "unknown",
                   "--comments", "Made-up network"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        allowed_roles = self.config.get("site", "change_default_netenv_roles")
        role_list = allowed_roles.strip().split()
        default_ne = self.config.get("site", "default_network_environment")
        self.matchoutput(out,
                         "Only users with %s can modify networks in the %s "
                         "network environment." % (role_list, default_ne),
                         command)

    def test_autherror_300(self):
        # Yet another entirely fictitious network
        command = ["add_network", "--ip", "192.168.3.0",
                   "--network_environment", "cardenv",
                   "--network", "cardnetwork3", "--netmask", "255.255.255.0",
                   "--building", "cards", "--side", "a", "--type", "unknown",
                   "--comments", "Made-up network"]
        self.noouttest(command)

    def test_autherror_900(self):
        self.promote_current_user()

    def testaddexcx(self):
        net = self.net.unknown[0]
        subnet = net.subnet()[0]
        command = ["add", "network", "--network", "excx-net",
                   "--ip", subnet.ip, "--netmask", subnet.netmask,
                   "--building", "np", "--type", net.nettype,
                   "--network_environment", "excx"]
        self.noouttest(command)

    def testaddnetsvcmap(self):
        net = self.net.netsvcmap
        subnet = net.subnet()[0]
        command = ["add", "network", "--network", "netsvcmap",
                   "--ip", subnet.ip, "--netmask", subnet.netmask,
                   "--building", "ut", "--type", net.nettype]
        self.noouttest(command)

    def testaddnetperssvcmap(self):
        net = self.net.netperssvcmap
        subnet = net.subnet()[0]
        command = ["add", "network", "--network", "netperssvcmap",
                   "--ip", subnet.ip, "--netmask", subnet.netmask,
                   "--building", "ut", "--type", net.nettype]
        self.noouttest(command)

    def testaddutcolo(self):
        net = self.net.unknown[1]
        command = ["add", "network", "--network", "utcolo-net",
                   "--ip", net.ip, "--netmask", net.netmask,
                   "--building", "ut", "--type", net.nettype,
                   "--network_environment", "utcolo"]
        self.noouttest(command)

    def testbadip(self):
        command = ["add_network", "--ip", "10.0.0.1",
                   "--network", "bad-address", "--netmask", "255.255.255.0",
                   "--building", "ut", "--side", "a", "--type", "unknown"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "IP address 10.0.0.1 is not a network address.  "
                         "Maybe you meant 10.0.0.0?", command)

    def testshownetwork(self):
        for network in self.net.all:
            command = "show network --ip %s" % network.ip
            out = self.commandtest(command.split(" "))
            self.matchoutput(out, "Network: %s" % network.ip, command)
            self.matchoutput(out, "Network Environment: internal", command)
            self.matchoutput(out, "IP: %s" % network.ip, command)
            self.matchoutput(out, "Netmask: %s" % network.netmask, command)
            self.matchoutput(out, "Sysloc: ut.ny.na", command)
            self.matchoutput(out, "Building: ut", command)
            self.matchoutput(out,
                             "Location Parents: [Organization ms, Hub ny, "
                             "Continent na, Country us, Campus ny, City ny]",
                             command)
            self.matchoutput(out, "Side: a", command)
            self.matchoutput(out, "Network Type: %s" % network.nettype,
                             command)

    def testshownetworkcomments(self):
        command = "show network --network np06bals03_v103"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Comments: Some network comments", command)

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

    def testaddlocalnet(self):
        command = ["add", "network", "--network", "localnet", "--ip",
                   "127.0.0.0", "--netmask", "255.0.0.0",
                   "--building", "ut"]
        self.noouttest(command)

    def testshownetworknoenv(self):
        command = "show network --building np"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "excx-net", command)

        command = "show network --building ut"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "utcolo-net", command)
        self.matchoutput(out, "netsvcmap", command)
        self.matchoutput(out, "netperssvcmap", command)

    def testshownetworkwithenv(self):
        command = "show network --building np --network_environment excx"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "excx-net", command)

    def testshowexcxnoenv(self):
        command = "show network --network excx-net"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Network excx-net not found.", command)

    def testshowexcxwithenv(self):
        net = self.net.unknown[0]
        subnet = net.subnet()[0]
        command = "show network --network excx-net --network_environment excx"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Network: excx-net", command)
        self.matchoutput(out, "Network Environment: excx", command)
        self.matchoutput(out, "IP: %s" % subnet.ip, command)
        self.matchoutput(out, "Netmask: %s" % subnet.netmask, command)

    def testshowutcolowithenv(self):
        net = self.net.unknown[1]
        command = "show network --network utcolo-net --network_environment utcolo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Network: utcolo-net", command)
        self.matchoutput(out, "Network Environment: utcolo", command)
        self.matchoutput(out, "IP: %s" % net.ip, command)
        self.matchoutput(out, "Netmask: %s" % net.netmask, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
