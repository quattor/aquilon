#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Module for testing the bind client command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest
from brokertest import TestBrokerCommand


class TestBindClient(TestBrokerCommand):
    """Testing manually binding client to services.

    Once a client has been bound, you can't use it to test
    the auto-selection logic in make/reconfigure.  Those tests
    are done exclusively with the chooser* services, which
    should not be used here.

    """

    def test_100_bind_afs(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "afs", "--instance", "q.ny.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance afs/q.ny.ms.com",
                         command)

    def test_105_verify_cat_afs(self):
        command = ["cat", "--service", "afs", "--instance", "q.ny.ms.com",
                   "--server"]
        out = self.commandtest(command)
        self.searchoutput(out,
                          r'"clients" = list\(\s*"unittest02.one-nyp.ms.com"\s*\);',
                          command)

    def test_110_bind_bootserver(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "bootserver", "--instance", "unittest"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance bootserver/unittest",
                         command)

    def test_115_bind_bootserver_auto(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "bootserver"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance bootserver/unittest",
                         command)

    def test_120_bind_dns(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "dns", "--instance", "unittest"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance dns/unittest",
                         command)

    def test_130_bind_ntp(self):
        command = ["bind", "client", "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "ntp", "--instance", "pa.ny.na"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest02.one-nyp.ms.com adding binding for "
                         "service instance ntp/pa.ny.na",
                         command)

    def test_135_bind_ntp_auto(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "ntp"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance ntp/pa.ny.na",
                         command)

    def test_140_bind_utsi1(self):
        command = ["bind", "client", "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi1"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "unittest00.one-nyp.ms.com adding binding for "
                         "service instance utsvc/utsi1",
                         command)

    def test_145_bind_utsi2_debug(self):
        command = ["bind", "client", "--debug",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        _, err = self.successtest(command)
        self.matchoutput(err, "Creating service chooser", command)

    def test_300_verify_unittest02(self):
        command = "show host --hostname unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: afs Instance: q.ny.ms.com",
                         command)
        self.matchoutput(out,
                         "Uses Service: bootserver Instance: unittest",
                         command)
        self.matchoutput(out,
                         "Uses Service: dns Instance: unittest",
                         command)
        self.matchoutput(out,
                         "Uses Service: ntp Instance: pa.ny.na",
                         command)
        self.matchoutput(out,
                         "Uses Service: utsvc Instance: utsi2",
                         command)

    def test_300_verify_unittest00(self):
        # For unittest00, will test that afs and dns are bound by make/reconfigure
        # because they are required services.
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Uses Service: bootserver Instance: unittest",
                         command)
        self.matchoutput(out,
                         "Uses Service: ntp Instance: pa.ny.na",
                         command)
        self.matchoutput(out,
                         "Uses Service: utsvc Instance: utsi1",
                         command)

    # FIXME: the broker does not populate the client list for performance
    # reasons
    # def testverifybindutsi1proto(self):
    #     command = "show service --service utsvc --instance utsi1 --format proto"
    #     svc = self.protobuftest(command.split(" "), expect=1)[0]
    #     self.assertEqual(svc.name, "utsvc",
    #                      "Service name mismatch: %s instead of utsvc\n" %
    #                      svc.name)
    #     si = svc.serviceinstances[0]
    #     self.assertEqual(si.name, "utsi1",
    #                      "Service name mismatch: %s instead of utsi1\n" %
    #                      si.name)
    #     clients = [host.fqdn for host in si.clients]
    #     self.assertEqual(clients, ["unittest00.one-nyp.ms.com"],
    #                      "Wrong list of clients for service utsvc "
    #                      "instance utsi1: %s\n" %
    #                      " ".join(clients))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindClient)
    unittest.TextTestRunner(verbosity=2).run(suite)
