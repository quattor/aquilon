#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
""" This is needed to make sure that a server is bound to the aqd service
    before make/reconfigure runs."""

from collections import defaultdict
import re

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

instance_servers = {
    "aqd": {
        "ny-prod": ["nyaqd1.ms.com"],
    },
    "bootserver": {
        "unittest": ["infra1.aqd-unittest.ms.com", "infra2.aqd-unittest.ms.com"],
        "one-nyp": ["infra1.one-nyp.ms.com", "infra2.one-nyp.ms.com"],
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
    "ips": {
        "northamerica": ["infra1.aqd-unittest.ms.com"],
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


class TestPrebindServer(TestBrokerCommand):

    def test_100_bind_servers(self):
        server_provides = defaultdict(lambda: defaultdict(list))
        for service, instances in instance_servers.items():
            for instance, servers in instances.items():
                for server in servers:
                    command = ["bind_server", "--hostname", server,
                               "--service", service, "--instance", instance] + self.valid_just_tcm
                    out = self.statustest(command)
                    # This test runs early when none of the servers are
                    # configured yet, so bind_server will complain - but only if
                    # the server is of a compileable archetype.
                    if re.match(r"[^.]+\.ms\.com$", server):
                        self.assertEmptyErr(out, command)
                    else:
                        self.matchoutput(out, "Warning: Host %s is missing the "
                                         "following required services" % server,
                                         command)

                    server_provides[server][service].append(instance)

                command = ["show_service", "--service", service,
                           "--instance", instance]
                out = self.commandtest(command)
                for server in servers:
                    self.matchoutput(out, "Server Binding: %s" % server, command)

                command = ["cat", "--service", service, "--instance", instance]
                out = self.commandtest(command)
                self.searchoutput(out,
                                  r'"servers" = list\(\s*' +
                                  r',\s*'.join('"%s"' % server for server in
                                               servers) +
                                  r'\s*\);',
                                  command)

        for server, services in server_provides.items():
            command = ["show_host", "--hostname", server]
            out = self.commandtest(command)
            for service, instances in services.items():
                for instance in instances:
                    self.matchoutput(out, "Provides Service: %s Instance: %s" %
                                     (service, instance),
                                     command)

    def test_200_cat_dns(self):
        command = "cat --service dns --instance unittest"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"servers" = list\(\s*"infra1\.aqd-unittest\.ms\.com",\s*'
                          r'"nyaqd1\.ms\.com"\s*\);',
                          command)
        self.searchoutput(out,
                          r'"server_ips" = list\(\s*"%s",\s*"%s"\s*\);' %
                          (self.net["zebra_vip"].usable[3],
                           self.net["aurora2"].usable[244]),
                          command)

    # This test needs to go before clients are added
    def test_300_early_constraint(self):
        command = "del service --service aqd --instance ny-prod"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Service aqd, instance ny-prod is still being "
                         "provided by servers", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestPrebindServer)
    unittest.TextTestRunner(verbosity=2).run(suite)
