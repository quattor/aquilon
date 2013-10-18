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
"""Module for testing the add service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

default_services = {
    "aqd": ["ny-prod"],

    # This service will not have any instances...
    "badservice": [],

    # Testing server affinity - ut.a will be available to all
    # three of chooser[123], but it will be the only instance
    # (with corresponding server) in common to all three.
    "chooser1": ["ut.a", "ut.b", "ut.c"],
    # Skipping ut.b for chooser2
    "chooser2": ["ut.a", "ut.c"],
    # Skipping ut.c for chooser3
    "chooser3": ["ut.a", "ut.b"],

    "dns": ["unittest", "one-nyp"],
    "esx_management_server": ["ut.a", "ut.b", "np"],
    "lemon": ["ny-prod"],
    "ntp": ["pa.ny.na"],
    "support-group": ["ec-service"],
    "syslogng": ["ny-prod"],

    # These service instances will not have any maps...
    "unmapped": ["instance1"],

    "utnotify": ["localhost"],
    "utsvc": ["utsi1", "utsi2"],
    "vcenter": ["ut", "np"],
    "vmseasoning": ["salt", "pepper", "sugar"],
}


class TestAddService(TestBrokerCommand):

    def testadddefaults(self):
        for service, instances in default_services.items():
            self.noouttest(["add_service", "--service", service])
            for instance in instances:
                self.noouttest(["add_service", "--service", service,
                                "--instance", instance])

    def testverifydefaults(self):
        for service, instances in default_services.items():
            command = ["show_service", "--service", service]
            out = self.commandtest(command)
            for instance in instances:
                self.matchoutput(out,
                                 "Service: %s Instance: %s" % (service, instance),
                                 command)

    def testaddafsinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "q.ny.ms.com",
                   "--comments", "Some instance comments"]
        self.noouttest(command)

    def testaddextraafsinstance(self):
        command = "add service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def testaddafsbynetinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net",
                   "--comments", "For network based maps"]
        self.noouttest(command)

    def testaddafsbynetdupinstance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net2",
                   "--comments", "afs-by-net duplicate"]
        self.noouttest(command)

    def testaddnetmappersinstances(self):
        command = ["add", "service", "--service", "netmap",
                   "--instance", "q.ny.ms.com",
                   "--comments", "For location based maps"]
        self.noouttest(command)

        command = ["add", "service", "--service", "netmap",
                   "--instance", "p-q.ny.ms.com",
                   "--comments", "For location based maps with personality"]
        self.noouttest(command)

        command = ["add", "service", "--service", "netmap",
                   "--instance", "netmap-pers",
                   "--comments", "For network based maps"]
        self.noouttest(command)

    def testaddbootserver(self):
        """ add service without instance first """
        command = ["add", "service", "--service", "bootserver",
                   "--comments", "Some service comments"]
        self.noouttest(command)

    def testaddbootserverinstance(self):
        self.noouttest(["add_service", "--service", "bootserver", "--instance", "unittest"])
        self.noouttest(["add_service", "--service", "bootserver", "--instance", "one-nyp"])

    def testaddpollhelper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["add", "service", "--service", service])
        self.noouttest(["add", "service", "--service", service,
                        "--instance", "unittest"])

    def testaddduplicateservice(self):
        command = "add service --service afs"
        self.badrequesttest(command.split(" "))

    def testaddduplicateinstance(self):
        command = "add service --service afs --instance q.ny.ms.com"
        self.badrequesttest(command.split(" "))

    def testverifyaddafsinstance(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)
        self.matchoutput(out, "Service: afs Instance: afs-by-net", command)
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)
        # Make sure the right object got the comments
        self.matchoutput(out, "    Comments: Some instance comments", command)
        self.searchclean(out, r"^  Comments:", command)

    def testverifyaddbootserverinstance(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver Instance: unittest", command)
        self.matchoutput(out, "Service: bootserver Instance: one-nyp", command)
        self.searchoutput(out, r"^  Comments: Some service comments", command)

    def testcatutsvcserverdefault(self):
        command = ["cat", "--service", "utsvc", "--server", "--default"]
        out = self.commandtest(command)
        self.matchoutput(out, "template service/utsvc/server/config;", command)

    def testcatutsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testcatutsi1default(self):
        command = "cat --service utsvc --instance utsi1 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi1/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi1/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def testcatutsi1uiserver(self):
        command = "cat --service utsvc --instance utsi1 --server"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/srvconfig;",
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"clients" = list\(\s*\);', command)

    def testcatutsi1uiserverdefault(self):
        command = "cat --service utsvc --instance utsi1 --server --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "template service/utsvc/utsi1/server/config;",
                         command)
        self.matchoutput(out,
                         '"/system/provides/utsvc" = create("servicedata/utsvc/utsi1/srvconfig");',
                         command)
        self.matchoutput(out,
                         'include { "service/utsvc/server/config" };',
                         command)

    def testcatutsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def testcatutsi2default(self):
        command = "cat --service utsvc --instance utsi2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi2/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi2/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def testcatutsvc(self):
        command = "cat --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc/config;",
                         command)

    def testcatutsvcdefault(self):
        command = "cat --service utsvc --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/client/config;", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddService)
    unittest.TextTestRunner(verbosity=2).run(suite)
