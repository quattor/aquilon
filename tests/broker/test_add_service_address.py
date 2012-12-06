#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
"""Module for testing the add service address command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestAddServiceAddress(TestBrokerCommand):

    def testsystemzebramix(self):
        ip = self.net.unknown[0].usable[3]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "e2",
                   "--service_address", "unittest00-e1.one-nyp.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by public interface "
                         "eth1 of machine unittest00.one-nyp.ms.com." % ip,
                         command)

    def testaddzebra2(self):
        # Use an address that is smaller than the primary IP to verify that the
        # primary IP is not removed
        ip = self.net.unknown[13].usable[1]
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", ip, "le1")
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "zebra2.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--ip", ip,
                   "--name", "zebra2"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyzebra2(self):
        ip = self.net.unknown[13].usable[1]
        command = ["show", "service", "address", "--name", "zebra2",
                   "--hostname", "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Service Address: zebra2", command)
        self.matchoutput(out, "Bound to: Host unittest20.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Address: zebra2.aqd-unittest.ms.com [%s]" % ip,
                         command)
        self.matchoutput(out, "Interfaces: eth0, eth1", command)

    def testverifyzebra2dns(self):
        ip = self.net.unknown[13].usable[1]
        command = ["show", "fqdn", "--fqdn", "zebra2.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out, "Reverse", command)

    def testaddzebra3(self):
        # Adding an even lower IP should cause zebra2 to be renumbered in DSDB
        zebra2_ip = self.net.unknown[13].usable[1]
        zebra3_ip = self.net.unknown[13].usable[0]
        self.dsdb_expect_delete(zebra2_ip)
        self.dsdb_expect_add("zebra3.aqd-unittest.ms.com", zebra3_ip, "le1")
        self.dsdb_expect_add("zebra2.aqd-unittest.ms.com", zebra2_ip, "le2")
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--service_address", "zebra3.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--ip", zebra3_ip,
                   "--name", "zebra3", "--map_to_primary"]
        self.noouttest(command)
        self.dsdb_verify()

    def testverifyunittest20(self):
        ip = self.net.unknown[13].usable[2]
        zebra2_ip = self.net.unknown[13].usable[1]
        zebra3_ip = self.net.unknown[13].usable[0]
        command = ["show", "host", "--hostname",
                   "unittest20.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Provides: zebra2.aqd-unittest.ms.com [%s] "
                         "(label: zebra2, service_holder: host)" % zebra2_ip,
                         command)
        self.matchoutput(out,
                         "Provides: zebra3.aqd-unittest.ms.com [%s] "
                         "(label: zebra3, service_holder: host)" % zebra3_ip,
                         command)
        self.matchclean(out, "Auxiliary: zebra2.aqd-unittest.ms.com", command)
        self.matchclean(out, "Auxiliary: zebra3.aqd-unittest.ms.com", command)

        self.searchoutput(out,
                          r"Service Address: hostname$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: unittest20\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra2$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: zebra2\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra2_ip,
                          command)
        self.searchoutput(out,
                          r"Service Address: zebra3$"
                          r"\s+Bound to: Host unittest20\.aqd-unittest\.ms\.com$"
                          r"\s+Address: zebra3\.aqd-unittest\.ms\.com \[%s\]$"
                          r"\s+Interfaces: eth0, eth1$" % zebra3_ip,
                          command)

    def testfailbadname(self):
        ip = self.net.unknown[0].usable[-1]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "hostname",
                   "--service_address", "hostname-label.one-nyp.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "The hostname service address is reserved for Zebra.  "
                         "Please specify the --zebra_interfaces option when "
                         "calling add_host if you want the primary name of the "
                         "host to be managed by Zebra.",
                         command)

    def testfailbadinterface(self):
        ip = self.net.unknown[0].usable[-1]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth2", "--name", "badiface",
                   "--service_address", "badiface.one-nyp.ms.com",
                   "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Machine unittest20.aqd-unittest.ms.com does not have "
                         "an interface named eth2.",
                         command)

    def testfailbadnetenv(self):
        net = self.net.unknown[0]
        subnet = net.subnet()[0]
        command = ["add", "service", "address",
                   "--hostname", "unittest20.aqd-unittest.ms.com",
                   "--interfaces", "eth0,eth1", "--name", "badenv",
                   "--service_address", "badenv.one-nyp.ms.com",
                   "--ip", subnet[1], "--network_environment", "excx"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Public Interface eth0 of machine "
                         "unittest20.aqd-unittest.ms.com already has an IP "
                         "address from network environment internal.  Network "
                         "environments cannot be mixed.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddServiceAddress)
    unittest.TextTestRunner(verbosity=2).run(suite)
