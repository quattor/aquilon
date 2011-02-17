#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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

if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)

