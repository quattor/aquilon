#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012-2019  Contributor
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

from broker.machinetest import MachineTestMixin
from broker.personalitytest import PersonalityTestMixin
from broker.utils import MockHub
from brokertest import TestBrokerCommand


class TestUpdateBuilding(PersonalityTestMixin, MachineTestMixin,
                         TestBrokerCommand):
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

    def test_126_update_ut_nodnsdomain(self):
        # Clean up (caused problems in test_build_clusters after the update
        # that introduced 'add host --force-dns-domain')
        command = ['update_building', '--building', 'ut',
                   '--default_dns_domain', '']
        self.noouttest(command)

    def test_127_verify_ut_dnsdomain_gone(self):
        # Confirm it has been cleaned up (see: test_126_update_... above).
        command = ['show_building', '--building', 'ut']
        out = self.commandtest(command)
        self.matchclean(out, 'Default DNS Domain', command)
        self.matchclean(out, 'aqd-unittest.ms.com', command)

    def test_130_update_tu_dnsdomain(self):
        command = ["update", "building", "--building", "tu",
                   "--default_dns_domain", "aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_131_verify_tu_dnsdomain(self):
        command = ["show", "building", "--building", "tu"]
        out = self.commandtest(command)
        self.matchoutput(out, "Default DNS Domain: aqd-unittest.ms.com",
                         command)

    def _preconditions_for_force_dns_domain_tests(self, domain, building,
                                                  another_building):
        # First, we need to be sure that domain is not already assigned to
        # building.
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchclean(out, 'Default DNS Domain', command)
        self.matchclean(out, domain, command)
        # Make sure that domain is already assigned to another_building.
        command = ['show_building', '--building', another_building]
        out = self.commandtest(command)
        self.matchoutput(out, 'Default DNS Domain: {}'.format(domain), command)

    def test_133_force_dns_domain_requires_default_dns_domain(self):
        # An attempt to use --force_dns_domain without providing
        # --default_dns_domain should fail with a warning.
        command = ['update_building', '--building', 'any-building',
                   '--force_dns_domain']
        out = self.badoptiontest(command)
        self.matchoutput(out, 'force_dns_domain can only be used together with'
                              ' one of: default_dns_domain.', command)

    def test_133_cannot_use_dns_domain_already_used_by_another_building(
            self):
        # The domain we will use for testing:
        domain = 'aqd-unittest.ms.com'
        # The building to which we will try to assign the domain:
        building = 'ut'
        # The building that already uses the domain (i.e. has it assigned as
        # its default DNS domain):
        another_building = 'tu'

        self._preconditions_for_force_dns_domain_tests(domain, building,
                                                       another_building)

        # An attempt to assign domain to building should fail with a warning.
        command = ['update_building', '--building', building,
                   '--default_dns_domain', domain]
        out = self.badrequesttest(command)
        self.searchoutput(
            out,
            (r'DNS domain "' + domain + r'" is already.*'
             + r'being .* other buildings \(e.g. [^)]*' + another_building
             + r'.* use --force_dns_domain.*'
             + r'as the default DNS domain for building "' + building
             ),
            command)
        # The default DNS domain for building should still be unset at this
        # point.
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchclean(out, 'Default DNS Domain', command)
        self.matchclean(out, domain, command)

    def test_133_default_dns_domain_used_by_another_building_can_be_forced(
            self):
        # The domain we will use for testing:
        domain = 'aqd-unittest.ms.com'
        # The building to which we will try to assign the domain:
        building = 'ut'
        # The building that already uses the domain (i.e. has it assigned as
        # its default DNS domain):
        another_building = 'tu'

        self._preconditions_for_force_dns_domain_tests(domain, building,
                                                       another_building)

        # An attempt to assign domain to building should succeed.
        command = ['update_building', '--building', building,
                   '--default_dns_domain', domain, '--force_dns_domain']
        self.noouttest(command)
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchoutput(out, 'Default DNS Domain: {}'.format(domain), command)

        # Clean up.
        command = ['update_building', '--building', building,
                   '--default_dns_domain', '']
        self.noouttest(command)
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchclean(out, 'Default DNS Domain', command)
        self.matchclean(out, domain, command)

    def test_133_cannot_change_dns_domain_if_some_hosts_still_aligned_to_it(
            self):
        # If there are hosts in a building that align with the building's
        # default DNS domain, and then that building's default DNS domain is
        # subsequently changed, command 'aq update_building ...
        # --default_dns_domain ...' should emit a warning and abort unless
        # '--force_dns_domain' is used.
        mh = MockHub(self)
        building = mh.add_building()
        mh.add_hosts(2, building=building)
        old_dns_domain = mh.add_dns_domain('old.ms.cc')
        self.noouttest(['update_building', '--building', building,
                        '--default_dns_domain', old_dns_domain])
        # Add a host aligned with the default DNS domain old_dns_domain.
        mh.add_host(building=building)
        new_dns_domain = mh.add_dns_domain('new.ms.cc')
        command = ['update_building', '--building', building,
                   '--default_dns_domain', new_dns_domain]
        # An attempt to assign domain to building should fail with a warning.
        out = self.badrequesttest(command)

        self.searchoutput(
            out,
            (r'There is at least one host in building .*' + building
             + r'.* that is aligned with the default DNS domain currently.*'
             + r'Use --force_dns_domain to override .*'
             + r'the current default DNS domain to "' + new_dns_domain),
            command)
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchoutput(out, 'Default DNS Domain: {}'.format(old_dns_domain),
                         command)
        mh.delete()

    def test_133_dns_domain_change_can_be_forced_even_if_hosts_use_previous(
            self):
        # Option --force_dns_domain should allow the default DNS domain to
        # be changed even if there are still some host aligned to the
        # previous default DNS domain in the building.
        mh = MockHub(self)
        building = mh.add_building()
        mh.add_hosts(2, building=building)
        old_dns_domain = mh.add_dns_domain('old.ms.cc')
        self.noouttest(['update_building', '--building', building,
                        '--default_dns_domain', old_dns_domain])
        # Add a host aligned with the default DNS domain old_dns_domain.
        mh.add_host(building=building)
        new_dns_domain = mh.add_dns_domain('new.ms.cc')
        self.successtest(['update_building', '--building', building,
                          '--default_dns_domain', new_dns_domain,
                          '--force_dns_domain'])
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchoutput(out, 'Default DNS Domain: {}'.format(new_dns_domain),
                         command)
        mh.delete()

    def test_133_current_default_dns_domain_should_be_assumed_valid(self):
        # In order to improve performance,
        # Given I run aq update_building ... --default_dns_domain ...,
        # When the currently set default DNS domain is the same as the new one,
        # I want CommandUpdateBuilding to skip all its DNS domain validation
        # checks.
        mh = MockHub(self)
        building = mh.add_building()
        mh.add_hosts(2, building=building)
        old_dns_domain = mh.add_dns_domain('old.ms.cc')
        self.noouttest(['update_building', '--building', building,
                        '--default_dns_domain', old_dns_domain])
        # Add a host aligned with the default DNS domain old_dns_domain.
        mh.add_host(building=building)
        # Since 'building' now contains a host that is aligned with the default
        # DNS domain of 'building', the following command will only succeed if
        # the DNS domain verification checks are skipped because the system
        # detects that the given DNS domain is the same as the currently set
        # one.
        self.successtest(['update_building', '--building', building,
                          '--default_dns_domain', old_dns_domain])
        command = ['show_building', '--building', building]
        out = self.commandtest(command)
        self.matchoutput(out, 'Default DNS Domain: {}'.format(old_dns_domain),
                         command)
        # Add a new building with the same default DNS domain as the
        # previous one, and subsequently try to update its default DNS
        # domain to the same domain.
        second_building = mh.add_building()
        self.noouttest(['update_building', '--building', second_building,
                        '--default_dns_domain', old_dns_domain,
                        '--force_dns_domain'])
        # Even though this DNS domain is already assigned to both this and
        # another building, since the domain is already set as the default DNS
        # domain for this building it should be silently accepted.
        self.noouttest(['update_building', '--building', second_building,
                        '--default_dns_domain', old_dns_domain])
        mh.delete()

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
    def test_145_update_uri_nocode(self):
        command = ["update", "building", "--building", "Testo",
                   "--uri", "assetinventory://005555"]
        (out, err) = self.successtest(command)
        self.searchoutput(err, "Warning: 'IT_CODE' in '(.*)' is empty for "
                               "URI 'assetinventory://005555'! Proceeding "
                               "without validation.", command)

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
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_161_set_up_cluster_resource_service_addr(self):
        ip = self.net["zebra_vip"].usable[10]
        fqdn = "zebra4.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "service", "address", "--cluster", "campus-test", "--service_address",
                   fqdn, "--name", "test-cluster-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_165_set_up_cluster_resourcegroup(self):
        ip = self.net["zebra_vip"].usable[11]
        fqdn = "zebra5.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()
        command = ["add_resourcegroup", "--resourcegroup", "test-resource-group",
                   "--cluster", "campus-test"] + self.valid_just_sn
        self.noouttest(command)

    def test_166_set_up_cluster_resourcegrou_serv_addr(self):
        ip = self.net["zebra_vip"].usable[11]
        fqdn = "zebra5.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "service", "address", "--resourcegroup", "test-resource-group", "--service_address",
                   fqdn, "--name", "test-cluster-res-service"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()

    def test_170_set_up_host_resourcegroup(self):
        ip = self.net["zebra_vip"].usable[12]
        fqdn = "zebra6.aqd-unittest.ms.com"
        self.dsdb_expect_add(fqdn, ip)
        command = ["add", "address", "--ip", ip, "--fqdn", fqdn,
                   "--grn=grn:/ms/ei/aquilon/aqd"] + self.valid_just_sn
        self.noouttest(command)
        self.dsdb_verify()
        command = ["add_resourcegroup", "--resourcegroup", "test-host-resgr", "--hostname",
                   "unittest20.aqd-unittest.ms.com"] + self.valid_just_sn
        self.noouttest(command)

    def test_171_set_up_host_resourcegroup_serv_addr(self):
        ip = self.net["zebra_vip"].usable[12]
        fqdn = "zebra6.aqd-unittest.ms.com"
        self.dsdb_expect_delete(ip)
        self.dsdb_expect_add(fqdn, ip)
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
