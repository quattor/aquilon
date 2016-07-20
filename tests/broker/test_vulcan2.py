#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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
"""Module for testing the vulcan2 related commands."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from notificationtest import VerifyNotificationsMixin


class TestVulcan20(VerifyNotificationsMixin, TestBrokerCommand):

    def add_utcluster(self, name, metacluster):
        command = ["add_esx_cluster", "--cluster=%s" % name,
                   "--metacluster=%s" % metacluster, "--room=utroom1",
                   "--buildstatus=build",
                   "--domain=unittest", "--down_hosts_threshold=0",
                   "--archetype=esx_cluster",
                   "--personality=vulcan2-server-dev"]
        self.noouttest(command)

#    metacluster aligned svc tests
    def test_400_addvcenterservices(self):
        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

    def test_410_bindvcenterservices(self):
        command = ["bind_client", "--metacluster", "utmc8",
                   "--service", "vcenter", "--instance", "ut"]
        err = self.statustest(command)
        # The service should be bound to the metacluster and to the hosts, but
        # not to the clusters as they do not require it
        self.matchoutput(err, "Metacluster utmc8 adding binding for "
                         "service instance vcenter/ut", command)
        self.matchoutput(err, "Host evh80.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchoutput(err, "Host evh81.aqd-unittest.ms.com adding binding "
                         "for service instance vcenter/ut", command)
        self.matchclean(err, "utecl", command)

        command = ["show", "host", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Uses Service: vcenter Instance: ut",
                         command)

        command = "show metacluster --metacluster utmc8"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Member Alignment: Service vcenter Instance ut", command)

    def test_420_failmaxclientcount(self):
        command = ["update_service", "--service", "vcenter", "--instance", "ut",
                   "--max_clients", "17"]
        self.noouttest(command)

        command = ["map", "service", "--service", "vcenter", "--instance", "ut",
                   "--building", "ut"]
        self.noouttest(command)

        self.add_utcluster("utpgcl2", "utmc8")

        command = ["make", "cluster", "--cluster", "utmc8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Please use the --metacluster option for "
                         "metaclusters.", command)
        self.matchoutput(out,
                         "The available instances ['ut'] for service vcenter "
                         "are at full capacity.",
                         command)

        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut"]
        self.noouttest(command)

        self.statustest(["del_cluster", "--cluster=utpgcl2"])

    def test_430_unbindvcenterservices(self):
        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["del_required_service", "--service", "vcenter",
                   "--archetype", "vmhost", "--personality", "vulcan2-server-dev"]
        self.noouttest(command)

        self.noouttest(["unbind_client", "--metacluster", "utmc8",
                        "--service", "vcenter"])

    def test_440_unmapvcenterservices(self):
        command = ["unmap", "service", "--service", "vcenter",
                   "--instance", "ut", "--building", "ut",
                   "--personality", "vulcan2-server-dev", "--archetype", "vmhost"]
        self.noouttest(command)

        command = ["make", "--hostname", "evh80.aqd-unittest.ms.com"]
        err = self.statustest(command)
        self.matchoutput(err, "Host evh80.aqd-unittest.ms.com removing "
                         "binding for service instance vcenter/ut", command)

        command = ["show", "host", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchclean(out,
                        "Uses Service: vcenter Instance: ut",
                        command)

    #
    # service binding conflicts
    #
    def test_500_add_mc_esx_service(self):
        command = ["add", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

        command = ["add_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["map", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        command = ["rebind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err,
                         "Metacluster utmc8 adding binding for service "
                         "instance esx_management_server/ut.mc",
                         command)
        for cluster in ["utecl12", "utecl13"]:
            self.searchoutput(err,
                              "ESX Cluster %s removing binding for service "
                              "instance esx_management_server/ut.[ab]" % cluster,
                              command)
            self.matchoutput(err,
                             "ESX Cluster %s adding binding for service "
                             "instance esx_management_server/ut.mc" % cluster,
                             command)
        for host in ["evh80", "evh81"]:
            self.searchoutput(err,
                              "Host %s.aqd-unittest.ms.com removing binding for "
                              "service instance esx_management_server/ut.[ab]" % host,
                              command)
            self.matchoutput(err,
                             "Host %s.aqd-unittest.ms.com adding binding for "
                             "service instance esx_management_server/ut.mc" % host,
                             command)

    def test_510_fail_make_host(self):
        command = ["make", "--hostname", "evh80.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host evh80.aqd-unittest.ms.com.",
                         command)

    def test_510_fail_make_cluster(self):
        command = ["make", "cluster", "--cluster", "utecl12"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for ESX cluster utecl12.",
                         command)
        self.matchoutput(out,
                         "ESX Metacluster utmc8 is set to use service instance "
                         "esx_management_server/ut.mc, but that instance is "
                         "not in a service map for "
                         "host evh80.aqd-unittest.ms.com.",
                         command)

    def test_520_verify_client_count(self):
        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 16$", command)

    def test_530_verify_mixed_client_count(self):
        self.add_utcluster("utpgcl3", "utmc8")
        command = ["bind_client", "--cluster", "utpgcl3", "--service",
                   "esx_management_server", "--instance", "ut.mc"]
        err = self.statustest(command)
        self.matchoutput(err, "ESX Cluster utpgcl3 adding binding for service "
                         "instance esx_management_server/ut.mc", command)

        command = ["show_service", "--service=esx_management_server",
                   "--instance=ut.mc"]
        out = self.commandtest(command)
        self.searchoutput(out, r"^  Client Count: 24$", command)

        # Can't unbind an an aligned service here and don't want unalign it

    def test_538_del_utpgcl3(self):
        self.statustest(["del_cluster", "--cluster=utpgcl3"])

    def test_540_remove_mc_esx_service(self):
        command = ["del_required_service", "--service", "esx_management_server",
                   "--archetype", "metacluster", "--personality", "vulcan2"]
        self.noouttest(command)

        command = ["unbind_client", "--metacluster", "utmc8",
                   "--service", "esx_management_server"]
        self.noouttest(command)

        command = ["unmap", "service", "--service", "esx_management_server", "--instance", "ut.mc",
                   "--building", "ut", "--personality", "vulcan2",
                   "--archetype", "metacluster"]
        self.noouttest(command)

        out = self.statustest(["make_cluster", "--cluster", "utecl12"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.searchoutput(out, "adding binding for service instance "
                          "esx_management_server/ut.[ab]", command)
        out = self.statustest(["make_cluster", "--cluster", "utecl13"])
        self.matchoutput(out, "removing binding for service instance "
                         "esx_management_server/ut.mc", command)
        self.searchoutput(out, "adding binding for service instance "
                          "esx_management_server/ut.[ab]", command)

        command = ["del", "service", "--service", "esx_management_server", "--instance", "ut.mc"]
        self.noouttest(command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestVulcan20)
    unittest.TextTestRunner(verbosity=2).run(suite)
