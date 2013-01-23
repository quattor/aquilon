#!/usr/bin/env python2.6
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Module for testing the refresh network command.

These tests don't do much, but they do verify that the command doesn't fail
immediately.

"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address, IPv4Network

from brokertest import TestBrokerCommand

def dynname(ip, domain="aqd-unittest.ms.com"):
    return "dynamic-%s.%s" % (str(ip).replace(".", "-"), domain)


class TestRefreshNetwork(TestBrokerCommand):

    # NOTE: The --all switch is not tested here because it would
    # delay a standard run by minutes.  Please test manually.

    # NOTE: There's currently no way to test updates.  Please test
    # any changes manually.

    def striplock(self, err):
        filtered = []
        for line in err.splitlines():
            if line.find("Acquiring lock") == 0:
                continue
            if line.find("Lock acquired.") == 0:
                continue
            if line.find("Released lock") == 0:
                continue
            filtered.append(line)
        return "".join("%s\n" % line for line in filtered)

    def check_network(self, addr, net_name, net_ip, prefix):
        name = "test-%s.aqd-unittest.ms.com" % addr.replace('.', '-')
        command = ["show", "address", "--fqdn", name]
        out = self.commandtest(command)
        self.matchoutput(out, "Network: %s [%s/%d]" % (net_name, net_ip,
                                                       prefix), command)

    # 100 sync up building np
    def test_100_syncfirst(self):
        command = "refresh network --building np"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        # There may be output here if the networks have changed between
        # populating the database and now.

    # 110 sync up building np expecting no output
    def test_110_syncclean(self):
        command = "refresh network --building np"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        # Technically this could have changed in the last few seconds,
        # but the test seems worth the risk. :)
        err = self.striplock(err)
        self.assertEmptyErr(err, command)

    # 120 sync up building np dryrun expecting no output
    def test_120_dryrun(self):
        command = "refresh network --building np --dryrun"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        # Technically this also could have changed in the last few seconds,
        # but the test again seems worth the risk. :)
        err = self.striplock(err)
        self.assertEmptyErr(err, command)

    def test_130_updates(self):
        self.noouttest(["del", "network", "--ip", "172.31.29.0"])
        self.noouttest(["add", "network", "--network", "wrong-params",
                        "--ip", "172.31.29.0", "--netmask", "255.255.255.128",
                        "--side", "a", "--type", "transit", "--building", "ut"])
        self.noouttest(["add", "router", "--ip", "172.31.29.3",
                        "--fqdn", "extrartr.aqd-unittest.ms.com"])

    def test_135_syncagain(self):
        command = "refresh network --building np"
        (out, err) = self.successtest(command.split(" "))
        self.matchoutput(err, "Setting network wrong-params [172.31.29.0/25] "
                         "name to nplab-vlan1", command)

        msg = "Setting network nplab-vlan1 [172.31.29.0/25] "
        self.matchoutput(err, msg + "type to unknown", command)
        self.matchoutput(err, msg + "side to b", command)
        self.matchoutput(err, msg + "location to building np", command)

        self.matchoutput(err, "Removing router 172.31.29.3 from network "
                         "nplab-vlan1", command)

    def test_138_router_gone(self):
        command = "search system --fqdn extrartr.aqd-unittest.ms.com"
        self.noouttest(command.split())

    # 150 test adds with the sync of another building
    def test_150_addhq(self):
        command = "refresh network --building hq"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        err = self.striplock(err)
        self.matchoutput(err, "Adding", command)
        self.matchclean(err, "Setting", command)
        # Make sure the refresh logic does not try to remove networks in other
        # buildings
        self.matchclean(err, "Deleting", command)

    # 200 add a dummy 0.1.1.0/24 network to np
    def test_200_adddummynetwork(self):
        command = ["add_network", "--network=0.1.1.0", "--ip=0.1.1.0",
                   "--prefixlen=24", "--building=np"]
        self.noouttest(command)
        command = ["add", "router", "--ip", "0.1.1.1",
                   "--fqdn", "dummydyn.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_250_addtestnets(self):
        networks = [
            # Merge various sized subnets, one is missing
            "0.1.2.0/25", "0.1.2.192/26",
            # Merge various sized subnets, first is missing
            "0.1.3.64/26", "0.1.3.128/25",
            # Split in QIP
            "0.1.4.0/24",
            # Another split in QIP
            "0.1.5.0/24"
        ]
        for net in networks:
            ipnet = IPv4Network(net)
            self.noouttest(["add", "network", "--network", ipnet.ip,
                            "--ip", ipnet.ip, "--prefixlen", ipnet.prefixlen,
                            "--building", "nettest"])

    def test_255_add_addresses(self):
        ips = ["0.1.2.1", "0.1.2.193",
               "0.1.3.65", "0.1.3.129",
               "0.1.4.1", "0.1.4.193",
               "0.1.5.129", "0.1.5.193"]
        for ip in ips:
            name = "test-%s.aqd-unittest.ms.com" % ip.replace('.', '-')
            self.dsdb_expect_add(name, ip)
            self.noouttest(["add", "address", "--ip", ip, "--fqdn", name])
        self.dsdb_verify()

    def test_260_test_split_merge(self):
        command = ["refresh", "network", "--building", "nettest"]
        (out, err) = self.successtest(command)
        # 0.1.2.x
        self.matchoutput(err, "Setting network 0.1.2.0 [0.1.2.0/25] "
                         "name to merge_1", command)
        self.matchoutput(err, "Adding router 0.1.2.1 to network merge_1",
                         command)
        self.matchoutput(err, "Setting network merge_1 [0.1.2.0/25] "
                         "prefix length to 24", command)
        self.matchoutput(err, "Deleting network 0.1.2.192 [0.1.2.192/26]",
                         command)
        # 0.1.3.x
        self.matchclean(err, "Setting network 0.1.3.0", command)
        self.matchoutput(err, "Adding network merge_2 [0.1.3.0/24]", command)
        self.matchoutput(err, "Adding router 0.1.3.1 to network merge_2",
                         command)
        self.matchoutput(err, "Deleting network 0.1.3.64 [0.1.3.64/26]",
                         command)
        self.matchoutput(err, "Deleting network 0.1.3.128 [0.1.3.128/25]",
                         command)
        # 0.1.4.x
        self.matchoutput(err, "Setting network 0.1.4.0 [0.1.4.0/24] "
                         "name to split_1", command)
        self.matchoutput(err, "Adding router 0.1.4.1 to network split_1",
                         command)
        self.matchoutput(err, "Setting network split_1 [0.1.4.0/24] "
                         "prefix length to 25", command)
        self.matchoutput(err, "Adding network split_2 [0.1.4.192/26]", command)
        self.matchoutput(err, "Adding router 0.1.4.193 to network split_2",
                         command)
        # 0.1.5.x
        self.matchclean(err, "Setting network 0.1.5.0", command)
        self.matchoutput(err, "Adding network split_3 [0.1.5.128/26]", command)
        self.matchoutput(err, "Adding router 0.1.5.129 to network split_3",
                         command)
        self.matchoutput(err, "Adding network split_4 [0.1.5.192/26]", command)
        self.matchoutput(err, "Adding router 0.1.5.193 to network split_4",
                         command)
        self.matchoutput(err, "Deleting network 0.1.5.0", command)

    def test_270_check_addresses(self):
        self.check_network("0.1.2.1", "merge_1", "0.1.2.0", 24)
        self.check_network("0.1.2.193", "merge_1", "0.1.2.0", 24)
        self.check_network("0.1.3.65", "merge_2", "0.1.3.0", 24)
        self.check_network("0.1.3.129", "merge_2", "0.1.3.0", 24)
        self.check_network("0.1.4.1", "split_1", "0.1.4.0", 25)
        self.check_network("0.1.4.193", "split_2", "0.1.4.192", 26)
        self.check_network("0.1.5.129", "split_3", "0.1.5.128", 26)
        self.check_network("0.1.5.193", "split_4", "0.1.5.192", 26)

    # 300 add a small dynamic range to 0.1.1.0
    def test_300_adddynamicrange(self):
        for ip in range(int(IPv4Address("0.1.1.4")),
                          int(IPv4Address("0.1.1.8")) + 1):
            self.dsdb_expect_add(dynname(IPv4Address(ip)), IPv4Address(ip))
        command = ["add_dynamic_range", "--startip=0.1.1.4", "--endip=0.1.1.8",
                   "--dns_domain=aqd-unittest.ms.com"]
        self.successtest(command)
        self.dsdb_verify()

    def test_310_verifynetwork(self):
        command = "show network --ip 0.1.1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Ranges: 0.1.1.4-0.1.1.8", command)

    def failsync(self, command):
        """Common code for the two tests below."""
        err = self.partialerrortest(command.split(" "))
        err = self.striplock(err)
        self.matchclean(err,
                        "Deleting network 0.1.1.0",
                        command)
        for i in range(4, 9):
            self.matchoutput(err,
                             "Network 0.1.1.0 cannot be deleted because DNS "
                             "record dynamic-0-1-1-%d.aqd-unittest.ms.com "
                             "[0.1.1.%d] still exists." %
                             (i, i),
                             command)
        return err

    # 400 normal should fail
    def test_400_syncclean(self):
        command = "refresh network --building np"
        err = self.failsync(command)
        self.matchoutput(err, "No changes applied because of errors.", command)

    # 410 dryrun should fail, no real difference in this case...
    def test_410_refreshnetworkdryrun(self):
        command = "refresh network --building np --dryrun"
        err = self.failsync(command)
        self.matchoutput(err, "No changes applied because of errors.", command)

    # 450 verify network still exists
    def test_450_verifynetwork(self):
        command = "show network --ip 0.1.1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "IP: 0.1.1.0", command)

    # 500 incrental should be a partial fail
    def test_500_incremental_fail(self):
        command = "refresh network --building np --incremental"
        err = self.failsync(command)
        self.matchclean(err, "No changes applied because of errors.", command)

    # 550 verify network still exists
    def test_550_verifynetwork(self):
        command = "show network --ip 0.1.1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "IP: 0.1.1.0", command)

    # 650 delete the dynamic range
    def test_650_deldynamicrange(self):
        for ip in range(int(IPv4Address("0.1.1.4")),
                          int(IPv4Address("0.1.1.8")) + 1):
            self.dsdb_expect_delete(IPv4Address(ip))
        command = ["del_dynamic_range", "--startip=0.1.1.4", "--endip=0.1.1.8"]
        self.successtest(command)
        self.dsdb_verify()

    def test_670_cleanup_addresses(self):
        ips = ["0.1.2.1", "0.1.2.193",
               "0.1.3.65", "0.1.3.129",
               "0.1.4.1", "0.1.4.193",
               "0.1.5.129", "0.1.5.193"]
        for ip in ips:
            name = "test-%s.aqd-unittest.ms.com" % ip.replace('.', '-')
            self.dsdb_expect_delete(ip)
            self.noouttest(["del", "address", "--ip", ip, "--fqdn", name])
        self.dsdb_verify()

    def test_680_cleanup_nettest(self):
        networks = ["0.1.2.0", "0.1.3.0", "0.1.4.0", "0.1.4.192", "0.1.5.128",
                    "0.1.5.192"]
        for net in networks:
            self.noouttest(["del", "network", "--ip", net])

    # 700 sync up building np
    # One last time to clean up the dummy network
    def test_700_syncclean(self):
        command = "refresh network --building np"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        err = self.striplock(err)
        self.matchoutput(err, "Deleting network 0.1.1.0", command)
        self.matchoutput(err, "Removing router 0.1.1.1", command)

    def test_710_cleanrouter(self):
        command = ["search", "system", "--fqdn", "dummydyn.aqd-unittest.ms.com"]
        self.noouttest(command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
