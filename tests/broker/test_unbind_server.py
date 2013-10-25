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

instance_servers = {
    "aqd": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
    "bootserver": {
        "unittest": ["infra1.aqd-unittest.ms.com"],
        "one-nyp": ["infra1.one-nyp.ms.com"],
    },
    "chooser1": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.b": ["server2.aqd-unittest.ms.com"],
        "ut.c": ["server3.aqd-unittest.ms.com"],
    },
    "chooser2": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.c": ["server3.aqd-unittest.ms.com"],
    },
    "chooser3": {
        "ut.a": ["server1.aqd-unittest.ms.com"],
        "ut.b": ["server2.aqd-unittest.ms.com"],
    },
    "dns": {
        "unittest": ["infra1.aqd-unittest.ms.com", "nyaqd1.ms.com"],
        "one-nyp": ["infra1.one-nyp.ms.com"],
    },
    "lemon": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
    "ntp": {
        "pa.ny.na": ["nyaqd1.ms.com"],
    },
    "syslogng": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
}


class TestUnbindServer(TestBrokerCommand):
    def check_last_server_msg(self, out, command, service, instance, host):
        self.matchoutput(out,
                         "WARNING: Host %s was the last server bound to "
                         "service instance %s/%s, which still has clients." %
                         (host, service, instance),
                         command)

    def test_100_check_initial_plenary(self):
        # This test must use the same regular expressions as
        # testverifycatunittest02() does, to verify that the success of
        # searchclean() is not due to errors in the expressions
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchoutput(out, r'/utsvc/[^/]+/server', command)

    def test_110_unbind_utsi1_unittest02(self):
        command = ["unbind", "server",
                   "--hostname", "unittest02.one-nyp.ms.com",
                   "--service", "utsvc", "--all"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi1",
                                   "unittest02.one-nyp.ms.com")

    def test_115_verify_cat_utsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def test_115_verify_cat_unittest02(self):
        command = ["cat", "--hostname", "unittest02.one-nyp.ms.com"]
        out = self.commandtest(command)
        self.searchclean(out, r'/utsvc/[^/]+/server', command)

    def test_115_verify_show_utsi1(self):
        command = "show service --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def test_120_unbind_utsi2_unittest00(self):
        command = ["unbind", "server",
                   "--hostname", "unittest00.one-nyp.ms.com",
                   "--service", "utsvc", "--instance", "utsi2"]
        err = self.statustest(command)
        self.check_last_server_msg(err, command, "utsvc", "utsi2",
                                   "unittest00.one-nyp.ms.com")

    def test_125_verify_cat_utsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def test_125_verify_show_utsi2(self):
        command = "show service --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchclean(out, "unittest02.one-nyp.ms.com", command)
        self.matchclean(out, "unittest00.one-nyp.ms.com", command)

    def test_130_unbind_pollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.statustest(["unbind", "server", "--hostname", "nyaqd1.ms.com",
                         "--service", service, "--instance", "unittest"])

    def test_150_unbind_all(self):
        for service, instances in instance_servers.items():
            for instance, servers in instances.items():
                for server in servers:
                    command = ["unbind_server", "--hostname", server,
                               "--service", service, "--instance", instance]
                    self.statustest(command)

            command = ["show_service", "--service", service]
            out = self.commandtest(command)
            for instance, servers in instances.items():
                for server in servers:
                    self.matchclean(out, server, command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUnbindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
