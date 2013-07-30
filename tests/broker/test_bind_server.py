#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the bind server command.

Note: This runs after make_aquilon and reconfigure tests.  If server
bindings are needed *before* those tests, they need to be in with
the TestPrebindServer tests.

"""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestBindServer(TestBrokerCommand):

    def testbindutsi1unittest02(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest02.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    # Test binding multiple servers to a single instance
    def testbindutsi1unittest00(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi1"])

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*'
                          r'"unittest00.one-nyp.ms.com",\s*'
                          r'"unittest02.one-nyp.ms.com"\s*\);',
                          command)
        self.matchclean(out, "server_ips", command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)

    def testverifybindutsi1proto(self):
        command = "show service --service utsvc --instance utsi1 --format proto"
        out = self.commandtest(command.split(" "))
        msg = self.parse_service_msg(out, 1)
        svc = msg.services[0]
        self.failUnlessEqual(svc.name, "utsvc",
                             "Service name mismatch: %s instead of utsvc\n" %
                             svc.name)
        si = svc.serviceinstances[0]
        self.failUnlessEqual(si.name, "utsi1",
                             "Service name mismatch: %s instead of utsi1\n" %
                             si.name)
        # Using set() to avoid ordering issues
        servers = set([srv.fqdn for srv in si.servers])
        expected = set(["unittest00.one-nyp.ms.com",
                        "unittest02.one-nyp.ms.com"])
        self.failUnlessEqual(servers, expected,
                             "Wrong list of servers for service utsvc "
                             "instance utsi1: %s\n" %
                             " ".join(list(servers)))

    # Test binding a server to multiple instances
    def testbindutsi2unittest00(self):
        self.noouttest(["bind", "server",
            "--hostname", "unittest00.one-nyp.ms.com",
            "--service", "utsvc", "--instance", "utsi2"])

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out,
                          r'"servers" = list\(\s*'
                          r'"unittest00.one-nyp.ms.com"\s*\);',
                          command)
        self.matchclean(out, "server_ips", command)

    def testreconfigureunittest00(self):
        command = "reconfigure --hostname unittest00.one-nyp.ms.com"
        (out, err) = self.successtest(command.split(" "))
        self.assertEmptyOut(out, command)

    def testverifybindutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)

    def testverifyshowserviceserver(self):
        command = "show service --server unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest00.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi2", command)

    def testverifyshowserviceserviceserver(self):
        command = "show service --service utsvc --server unittest02.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Server: unittest02.one-nyp.ms.com", command)
        self.matchoutput(out, "Service: utsvc Instance: utsi1", command)

    def testverifycatunittest00(self):
        command = "cat --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "object template unittest00.one-nyp.ms.com",
                         command)
        self.matchoutput(out,
                         'include { "service/utsvc/utsi1/server/config" };',
                         command)
        self.matchoutput(out,
                         'include { "service/utsvc/utsi2/server/config" };',
                         command)

    def testverifyshowunittest00(self):
        command = "show host --hostname unittest00.one-nyp.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Primary Name: unittest00.one-nyp.ms.com",
                         command)
        self.matchoutput(out, "Provides: service/utsvc/utsi1", command)
        self.matchoutput(out, "Provides: service/utsvc/utsi2", command)

    def testverifyshowunittest00proto(self):
        command = "show host --hostname unittest00.one-nyp.ms.com --format proto"
        out = self.commandtest(command.split(" "))
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        self.failUnlessEqual(len(host.services_provided), 2)
        services = set()
        for svc_msg in host.services_provided:
            services.add("%s/%s" % (svc_msg.service, svc_msg.instance))
        for binding in ("utsvc/utsi1", "utsvc/utsi2"):
            self.failUnless(binding in services,
                            "Service binding %s is missing from protobuf "
                            "message. All bindings: %s" %
                            (binding, ",".join(list(services))))


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestBindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
