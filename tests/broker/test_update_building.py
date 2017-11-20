#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016,2017  Contributor
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
"""Module for testing the update building command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from broker.personalitytest import PersonalityTestMixin


class TestUpdateBuilding(PersonalityTestMixin, TestBrokerCommand):
    def test_100_updateaddress(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 24 Cherry Lane")
        command = ["update", "building", "--building", "tu",
                   "--address", "24 Cherry Lane"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_105_verifyupdateaddress(self):
        command = "show building --building tu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 24 Cherry Lane", command)

    def test_110_updatecity(self):
        self.dsdb_expect("update_building_aq -building_name tu "
                         "-building_addr 20 Penny Lane")
        self.dsdb_expect_del_campus_building("ny", "tu")
        self.dsdb_expect_add_campus_building("ta", "tu")

        command = ["update", "building", "--building", "tu",
                   "--address", "20 Penny Lane", "--city", "e5"]
        err = self.statustest(command)
        self.matchoutput(err, "There are 1 service(s) mapped to the "
                         "old location of the (city ny), "
                         "please review and manually update mappings for "
                         "the new location as needed.", command)
        self.dsdb_verify()

    def test_111_verifyupdatecity(self):
        command = "show building --building tu"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Building: tu", command)
        self.matchoutput(out, "Address: 20 Penny Lane", command)
        self.matchoutput(out, "City e5", command)

    def test_115_change_hub(self):
        self.dsdb_expect_del_campus_building("ta", "tu")
        self.dsdb_expect_add_campus_building("ln", "tu")

        command = ["update", "building", "--building", "tu",
                   "--city", "ln"]
        self.noouttest(command)
        self.dsdb_verify()

    def test_120_update_ut_dnsdomain(self):
        command = ["update", "building", "--building", "ut",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_125_verify_ut_dnsdomain(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_125_verify_ut_dnsdomain(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_130_update_tu_dnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_131_verify_tu_dnsdomain(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def test_135_update_tu_nodnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", ""]
        self.noouttest(command)

    def test_136_verify_tu_dnsdomain_gone(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchclean(out, "Default DNS Domain", command)
        self.matchclean(out, "aqd-unittest.ms.com", command)

    def test_140_update_ut_uri(self):
        command = ["update", "building", "--building", "ut",
                   "--uri", "assetinventory://003450"]
        self.noouttest(command)

    def test_141_verify_ut_uri(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Location URI: assetinventory://003450",
                         command)

    def test_142_update_ut_uri_invalid(self):
        command = ["update", "building", "--building", "ut",
                   "--uri", "assetinventory://003550"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Building name and URI do not match", command)

    def test_143_update_ut_uri_force(self):
        command = ["update", "building", "--building", "ut",
                   "--uri", "assetinventory://003550", "--force_uri"]
        self.noouttest(command)

    def test_144_verify_ut_uri_force(self):
        command = ["show", "building", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out, "Location URI: assetinventory://003550",
                         command)

    def test_150_set_up_prod_personality(self):
        GRN = "grn:/ms/ei/aquilon/aqd"
        PPROD = "justify-prod"
        QPROD = "justify-qa"
        personalities = {
            QPROD: {'grn': GRN,
                    'environment': 'qa',
                    'staged': True},
            PPROD: {'grn': GRN,
                    'environment': 'prod',
                    'staged': True},
        }
        for personality, kwargs in personalities.items():
            self.create_personality("aquilon", personality, **kwargs)

        # Force the next stage to be created
        self.noouttest(["update_personality", "--personality", PPROD,
                        "--archetype", "aquilon"])
        self.noouttest(["update_personality", "--personality", QPROD,
                        "--archetype", "aquilon"])

    def test_160_set_up_cluster_resource(self):
        ip = self.net["zebra_vip"].usable[10]
        fqdn = "zebra4.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_161_set_up_cluster_resource_service_addr(self):
        ip = self.net["zebra_vip"].usable[10]
        fqdn = "zebra4.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        command = ["add", "service", "address", "--cluster", "campus-test", "--service_address",
                   fqdn, "--name", "test-cluster-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_165_set_up_cluster_resourcegroup(self):
        ip = self.net["zebra_vip"].usable[11]
        fqdn = "zebra5.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()
        command = ["add_resourcegroup", "--resourcegroup", "test-resource-group",
                   "--cluster", "campus-test"] + self.valid_just_sn
        self.noouttest(command)

    def test_166_set_up_cluster_resourcegrou_serv_addr(self):
        ip = self.net["zebra_vip"].usable[11]
        fqdn = "zebra5.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        command = ["add", "service", "address", "--resourcegroup", "test-resource-group", "--service_address",
                   fqdn, "--name", "test-cluster-res-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_170_set_up_host_resourcegroup(self):
        ip = self.net["zebra_vip"].usable[12]
        fqdn = "zebra6.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()
        command = ["add_resourcegroup", "--resourcegroup", "test-host-resgr", "--hostname",
                   "unittest20.aqd-unittest.ms.com"] + self.valid_just_sn
        self.noouttest(command)

    def test_171_set_up_host_resourcegroup_serv_addr(self):
        ip = self.net["zebra_vip"].usable[12]
        fqdn = "zebra6.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        command = ["add_service_address", "--resourcegroup", "test-host-resgr", "--name", "test-service-host",
                   "--service_address", "zebra6.aqd-unittest.ms.com"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_175_show_prod_resources(self):
        command = "show network --network zebra_vip"
        out = self.commandtest(command.split())
        self.matchoutput(out, 'Building ut',
                         command)

        command = "show cluster --cluster campus-test"
        out = self.commandtest(command.split())
        self.matchoutput(out, 'Environment: prod',
                         command)
        self.matchoutput(out, 'Build Status: ready',
                         command)
        self.matchoutput(out, 'Building: bx',
                         command)
        self.matchoutput(out, 'Service Address: test-cluster-service',
                         command)
        self.matchoutput(out, 'Address: zebra4.aqd-unittest.ms.com [4.2.12.143]',
                         command)
        self.matchoutput(out, 'Address: zebra5.aqd-unittest.ms.com [4.2.12.144]',
                         command)
        self.matchoutput(out, 'Resource Group: test-resource-group',
                         command)

        command = "show host --host unittest20.aqd-unittest.ms.com"
        out = self.commandtest(command.split())
        self.matchoutput(out, 'Resource Group: test-host-resgr',
                         command)
        self.matchoutput(out, 'Service Address: test-service-host',
                         command)

    def test_200_hub_change_machines_cm_fail(self):
        h = "aquilon91.aqd-unittest.ms.com"
        command = ["update", "machine", "--machine", "ut9s03p41", "--desk", "utdesk2"]
        self.noouttest(command)

        command = "search machine --building ut"
        out = self.commandtest(command.split())
        self.matchoutput(out, "ut9s03p41", command)

        command = ["reconfigure", "--hostname", h, "--archetype", "aquilon", "--buildstatus", "ready",
               "--personality", "justify-prod", "--personality_stage", "next"]
        self.statustest(command)

        command = ["show", "host", "--host", h]
        out = self.commandtest(command)
        self.matchoutput(out, 'Environment: prod',
                         command)
        self.matchoutput(out, 'Build Status: ready',
                         command)
        self.matchoutput(out, 'Building: ut',
                         command)
        self.matchoutput(out, "ut9s03p41", command)

        # ut has prod/ready machines, so CM is required
        command = ["update", "building", "--building", "ut", "--city", "ny"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

    def test_210_change_machines_cm_success(self):
        command = ["update", "building", "--building", "ut",
                        "--city", "ny"] + self.valid_just_sn
        out = self.statustest(command)
        self.matchoutput(out, "There are 1 service(s) mapped to the old location of the (city ny), "
                              "please review and manually update mappings for the new location as needed.",
                         command)

    def test_211_clean_up_service_addresses(self):
        ip = self.net["zebra_vip"].usable[12]
        self.dsdb_expect_delete(ip)
        command = "del service address --resourcegroup test-host-resgr --name test-service-host"
        self.noouttest(command.split(" "))
        self.dsdb_verify()

    def test_212_clean_up_service_addresses(self):
        ip = self.net["zebra_vip"].usable[11]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address", "--resourcegroup", "test-resource-group",
                   "--name", "test-cluster-res-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_213_clean_up_service_addresses(self):
        ip = self.net["zebra_vip"].usable[10]
        self.dsdb_expect_delete(ip)
        command = ["del", "service", "address", "--cluster", "campus-test", "--name",
                   "test-cluster-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateBuilding)
    unittest.TextTestRunner(verbosity=2).run(suite)
