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
"""Module for testing the unbind server command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestUnbindServer(TestBrokerCommand):
    def check_last_server_msg(self, out, command, service, instance, host):
        self.matchoutput(out,
                         "WARNING: Host %s was the last server bound to "
                         "service instance %s/%s, which still has clients." %
                         (host, service, instance),
                         command)

    def testcheckinitialplenary(self):
        # This test must use the same regular expressions as
        # testverifycatunittest02() does, to verify that the success of
        # searchclean() is not due to errors in the expressions
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'/utsvc/[^/]+/server', command)

    def testunbindutsi1unittest02(self):
        command = ["unbind", "server",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi1",
                                   "unittest02.one-nyp.ms.com")

    # Should have already been unbound...
    # Hmm... this (as implemented) actually returns 0.  Kind of a pointless
    # test case, at least for now.
    #def testrejectunbindutsi1unittest00(self):
    #    self.badrequesttest(["unbind", "server",
    #        "--hostname", "unittest00.one-nyp.ms.com",
    #        "--service", "utsvc", "--instance", "utsi1"])

    def testverifycatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testverifycatunittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out, r'/utsvc/[^/]+/server', command)

    def testverifybindutsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testunbindutsi2unittest00(self):
        command = ["unbind", "server",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi2",
                                   "unittest00.one-nyp.ms.com")

    def testverifycatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testverifybindutsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def testunbinddns(self):
        command = ["unbind", "server", "--service", "dns", "--all",
                   "--hostname", "infra1.one-nyp.ms.com"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "dns", "one-nyp",
                                   "infra1.one-nyp.ms.com")

        self.noouttest(["unbind", "server",
                        "--hostname", "infra1.aqd-unittest.ms.com",
                        "--service", "dns", "--all"])

        command = ["unbind", "server", "--service", "dns", "--all",
                   "--hostname", "nyaqd1.ms.com"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "dns", "unittest",
                                   "nyaqd1.ms.com")

    def testunbindntp(self):
        command = ["unbind", "server",
                   "--hostname", "nyaqd1.ms.com", "--service", "ntp", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "ntp", "pa.ny.na",
                                   "nyaqd1.ms.com")

    def testverifyunbindntp(self):
        command = "show service --service ntp"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "nyaqd1.ms.com", command)

    def testunbindaqd(self):
        command = ["unbind", "server",
                   "--hostname", "nyaqd1.ms.com", "--service", "aqd", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "aqd", "ny-prod",
                                   "nyaqd1.ms.com")

    def testverifyunbindaqd(self):
        command = "show service --service aqd"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "nyaqd1.ms.com", command)

    def testunbindlemon(self):
        command = ["unbind", "server", "--hostname", "nyaqd1.ms.com",
                   "--service", "lemon", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "lemon", "ny-prod",
                                   "nyaqd1.ms.com")

    def testverifyunbindlemon(self):
        command = "show service --service lemon"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "nyaqd1.ms.com", command)

    def testunbindsyslogng(self):
        command = ["unbind", "server", "--hostname", "nyaqd1.ms.com",
                   "--service", "syslogng", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "syslogng", "ny-prod",
                                   "nyaqd1.ms.com")

    def testverifyunbindsyslogng(self):
        command = "show service --service syslogng"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "nyaqd1.ms.com", command)

    def testunbindbootserver(self):
        command = ["unbind_server",
                   "--hostname=infra1.aqd-unittest.ms.com",
                   "--service=bootserver", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "bootserver", "unittest",
                                   "infra1.aqd-unittest.ms.com")

        command = ["unbind_server",
                   "--hostname=infra1.one-nyp.ms.com",
                   "--service=bootserver", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "bootserver", "one-nyp",
                                   "infra1.one-nyp.ms.com")

    def testverifyunbindbootserver(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "infra1.aqd-unittest.ms.com", command)
        self.matchclean(out, "infra1.one-nyp.ms.com", command)

    def testunbindchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for (s, n) in [(1, 'a'), (2, 'b'), (3, 'c')]:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                server = "server%d.aqd-unittest.ms.com" % s
                instance = "ut.%s" % n
                command = ["unbind", "server", "--hostname", server,
                           "--service", service, "--instance", instance]
                self.statustest(command)

    def testunbindpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.statustest(["unbind", "server", "--hostname", "nyaqd1.ms.com",
                         "--service", service, "--instance", "unittest"])


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
