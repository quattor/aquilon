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

import os.path

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

    def test_100_add_defaults(self):
        service_plenaries = ["servicedata/%s/config",
                             "service/%s/client/config",
                             "service/%s/server/config"]
        instance_plenaries = ["servicedata/%s/%s/config",
                              "servicedata/%s/%s/srvconfig",
                              "service/%s/%s/client/config",
                              "service/%s/%s/server/config"]

        for service, instances in default_services.items():
            for pattern in service_plenaries:
                plenary = self.plenary_name(pattern % service)
                self.failIf(os.path.exists(plenary),
                            "Plenary '%s' was not expected to exist." % plenary)

            self.noouttest(["add_service", "--service", service])

            for instance in instances:
                for pattern in instance_plenaries:
                    plenary = self.plenary_name(pattern % (service, instance))
                    self.failIf(os.path.exists(plenary),
                                "Plenary '%s' was not expected to exist." % plenary)

                self.noouttest(["add_service", "--service", service,
                                "--instance", instance])

                for pattern in instance_plenaries:
                    plenary = self.plenary_name(pattern % (service, instance))
                    self.failUnless(os.path.exists(plenary),
                                    "Plenary '%s' does not exist." % plenary)

            for pattern in service_plenaries:
                plenary = self.plenary_name(pattern % service)
                self.failUnless(os.path.exists(plenary),
                                "Plenary '%s' does not exist." % plenary)

    def test_105_verify_defaults(self):
        for service, instances in default_services.items():
            command = ["show_service", "--service", service]
            out = self.commandtest(command)
            for instance in instances:
                self.matchoutput(out,
                                 "Service: %s Instance: %s" % (service, instance),
                                 command)

    def test_110_add_afs_instance(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "q.ny.ms.com",
                   "--comments", "Some instance comments"]
        self.noouttest(command)

    def test_120_add_extra_afs_instance(self):
        command = "add service --service afs --instance q.ln.ms.com"
        self.noouttest(command.split(" "))

    def test_120_add_afsbynet(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net",
                   "--comments", "For network based maps"]
        self.noouttest(command)

    def test_121_add_afsbynet_duplicate(self):
        command = ["add", "service", "--service", "afs",
                   "--instance", "afs-by-net2",
                   "--comments", "afs-by-net duplicate"]
        self.noouttest(command)

    def test_130_add_netmappers_instances(self):
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

    def test_140_add_bootserver(self):
        """ add service without instance first """
        command = ["add", "service", "--service", "bootserver",
                   "--comments", "Some service comments"]
        self.noouttest(command)

    def test_141_add_bootserver_instance(self):
        self.noouttest(["add_service", "--service", "bootserver", "--instance", "unittest"])
        self.noouttest(["add_service", "--service", "bootserver", "--instance", "one-nyp"])

    def test_150_add_poll_helper(self):
        service = self.config.get("broker", "poll_helper_service")
        self.noouttest(["add", "service", "--service", service])
        self.noouttest(["add", "service", "--service", service,
                        "--instance", "unittest"])

    def test_200_add_duplicate_service(self):
        command = "add service --service afs"
        self.badrequesttest(command.split(" "))

    def test_200_add_duplicate_instance(self):
        command = "add service --service afs --instance q.ny.ms.com"
        self.badrequesttest(command.split(" "))

    def test_300_show_afs(self):
        command = "show service --service afs"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: afs Instance: q.ny.ms.com", command)
        self.matchoutput(out, "Service: afs Instance: afs-by-net", command)
        self.matchoutput(out, "Service: afs Instance: q.ln.ms.com", command)
        # Make sure the right object got the comments
        self.matchoutput(out, "    Comments: Some instance comments", command)
        self.searchclean(out, r"^  Comments:", command)

    def test_300_show_bootserver(self):
        command = "show service --service bootserver"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Service: bootserver Instance: unittest", command)
        self.matchoutput(out, "Service: bootserver Instance: one-nyp", command)
        self.searchoutput(out, r"^  Comments: Some service comments", command)

    def test_300_cat_utsvc_server_default(self):
        command = ["cat", "--service", "utsvc", "--server", "--default"]
        out = self.commandtest(command)
        self.matchoutput(out, "template service/utsvc/server/config;", command)

    def test_300_cat_utsi1(self):
        command = "cat --service utsvc --instance utsi1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def test_300_cat_utsi1_default(self):
        command = "cat --service utsvc --instance utsi1 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi1/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi1/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def test_300_cat_utsi1_server(self):
        command = "cat --service utsvc --instance utsi1 --server"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi1/srvconfig;",
                         command)
        self.matchoutput(out, '"instance" = "utsi1";', command)
        self.searchoutput(out, r'"clients" = list\(\s*\);', command)

    def test_300_cat_utsi1_server_default(self):
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

    def test_300_cat_utsi2(self):
        command = "cat --service utsvc --instance utsi2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "structure template servicedata/utsvc/utsi2/config;",
                         command)
        self.matchoutput(out, 'include { "servicedata/utsvc/config" };',
                         command)
        self.matchoutput(out, '"instance" = "utsi2";', command)
        self.searchoutput(out, r'"servers" = list\(\s*\);', command)

    def test_300_cat_utsi2_default(self):
        command = "cat --service utsvc --instance utsi2 --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/utsi2/client/config;",
                         command)
        self.matchoutput(out,
                         '"/system/services/utsvc" = create("servicedata/utsvc/utsi2/config");',
                         command)
        self.matchoutput(out, 'include { "service/utsvc/client/config" };',
                         command)

    def test_300_cat_utsvc(self):
        command = "cat --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "structure template servicedata/utsvc/config;",
                         command)

    def test_300_cat_utsvc_default(self):
        command = "cat --service utsvc --default"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "template service/utsvc/client/config;", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddService)
    unittest.TextTestRunner(verbosity=2).run(suite)
