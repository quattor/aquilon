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
"""Module for testing the refresh network command.

These tests don't do much, but they do verify that the command doesn't fail
immediately.

"""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from ipaddr import IPv4Address

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

    # 150 test adds with the sync of another building
    def test_150_addhq(self):
        command = "refresh network --building hq"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        err = self.striplock(err)
        self.matchoutput(err, "Adding", command)
        self.matchclean(err, "Setting", command)
        self.matchclean(err, "Deleting", command)

    # 200 add a dummy 0.1.1.0/24 network to np
    def test_200_adddummynetwork(self):
        command = ["add_network", "--network=0.1.1.0", "--ip=0.1.1.0",
                   "--prefixlen=24", "--building=np"]
        self.noouttest(command)

    # 300 add a small dynamic range to 0.1.1.0
    def test_300_adddynamicrange(self):
        for ip in range(int(IPv4Address("0.1.1.4")),
                          int(IPv4Address("0.1.1.8")) + 1):
            self.dsdb_expect_add(dynname(IPv4Address(ip)), IPv4Address(ip))
        command = ["add_dynamic_range", "--startip=0.1.1.4", "--endip=0.1.1.8",
                   "--dns_domain=aqd-unittest.ms.com"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_310_verifynetwork(self):
        command = "show network --ip 0.1.1.0"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Dynamic Ranges: 0.1.1.4-0.1.1.8", command)

    def failsync(self, command):
        """Common code for the two tests below."""
        err = self.partialerrortest(command.split(" "))
        err = self.striplock(err)
        self.matchoutput(err,
                         "Deleting network 0.1.1.0",
                         command)
        for i in range(4, 9):
            self.matchoutput(err,
                             "No network found for IP address 0.1.1.%d "
                             "[dynamic-0-1-1-%d.aqd-unittest.ms.com]." %
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

    # 550 verify network is gone
    def test_550_verifynetwork(self):
        command = "show network --ip 0.1.1.0"
        out = self.notfoundtest(command.split(" "))

    # 600 re-add the dummy 0.1.1.0/26 network to np
    # Needed for the del dynamic range command to succeed.
    def test_600_adddummynetwork(self):
        command = ["add_network", "--network=0.1.1.0", "--ip=0.1.1.0",
                   "--mask=256", "--building=np"]
        self.noouttest(command)

    # 650 delete the dynamic range
    def test_650_deldynamicrange(self):
        for ip in range(int(IPv4Address("0.1.1.4")),
                          int(IPv4Address("0.1.1.8")) + 1):
            self.dsdb_expect_delete(IPv4Address(ip))
        command = ["del_dynamic_range", "--startip=0.1.1.4", "--endip=0.1.1.8"]
        self.noouttest(command)
        self.dsdb_verify()

    # 700 sync up building np
    # One last time to clean up the dummy network
    def test_700_syncclean(self):
        command = "refresh network --building np"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)
        err = self.striplock(err)
        self.matchoutput(err,
                         "Deleting network 0.1.1.0",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestRefreshNetwork)
    unittest.TextTestRunner(verbosity=2).run(suite)
