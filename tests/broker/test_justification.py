#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016,2017  Contributor
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
"""Module for testing the make command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from broker.brokertest import TestBrokerCommand
from broker.personalitytest import PersonalityTestMixin

GRN = "grn:/ms/ei/aquilon/aqd"
PPROD = "justify-prod"
QPROD = "justify-qa"


class TestJustification(PersonalityTestMixin, TestBrokerCommand):
    def test_100_setup(self):

        command = ["add", "feature", "--feature", "testfeature",
                   "--type", "host", "--grn", GRN, "--visibility", "public",
                   "--activation", "reboot", "--deactivation", "reboot"]
        self.noouttest(command)

        command = ["add", "feature", "--feature", "testclusterfeature",
                   "--type", "host", "--grn", GRN, "--visibility", "public",
                   "--activation", "reboot", "--deactivation", "reboot"]
        self.noouttest(command)

    def test_110_host_setup(self):
        host_list = ["aquilon91.aqd-unittest.ms.com", "unittest26.aqd-unittest.ms.com"]

        for host in host_list:
            command = ["reconfigure", "--hostname", host,
                       "--archetype", "aquilon", "--buildstatus", "ready",
                       "--personality", PPROD, "--personality_stage", "next"] + self.valid_just_tcm
            self.statustest(command)

    def test_200_update_personality(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_210_add_parameter(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_215_update_parameter(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_220_del_parameter(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_230_map_grn(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_240_unmap_grn(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_270_add_required_svc(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_280_del_required_svc(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_290_add_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.statustest(command)

    def test_300_del_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.statustest(command)

    def test_305_update_host_back(self):
        host = "unittest26.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", host,
                   "--archetype", "aquilon", "--buildstatus", "ready",
                   "--personality", "inventory"] + self.valid_just_tcm
        self.statustest(command)

    def test_310_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_320_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.noouttest(command)

    def test_330_bind_feature(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.statustest(command)

    def test_340_unbind_feature(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.valid_just_tcm
        self.statustest(command)

    def test_350_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def test_360_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def test_370_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "vmseasoning", "--instance", "pepper"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["map", "service", "--organization", "ms",
                   "--service", "vmseasoning", "--instance", "pepper",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def test_380_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "vmseasoning", "--instance", "pepper"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "vmseasoning", "--instance", "pepper",
                   "--justification", "tcm=12345678"]
        self.noouttest(command)

    def test_400_host_setup(self):
        h = "aquilon91.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", QPROD, "--personality_stage", "next"] \
                  + self.valid_just_tcm
        self.statustest(command)

    def test_405_update_personality(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", QPROD]
        self.noouttest(command)

    def test_410_add_parameter(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users",
                   "--value", "test"]
        self.noouttest(command)

    def test_415_update_parameter(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users",
                   "--value", "test"]
        self.noouttest(command)

    def test_420_del_parameter(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users"]
        self.noouttest(command)

    def test_430_map_grn(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        self.noouttest(command)

    def test_440_unmap_grn(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        self.noouttest(command)

    def test_470_add_required_svc(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", QPROD]
        self.noouttest(command)

    def test_480_del_required_svc(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", QPROD]
        self.noouttest(command)

    def test_490_add_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", QPROD]
        self.noouttest(command)

    def test_500_del_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", QPROD]
        self.noouttest(command)

    def test_510_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.noouttest(command)

    def test_520_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.noouttest(command)

    def test_530_bind_feature(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.statustest(command)

    def test_540_unbind_feature(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.statustest(command)

    def test_600_host_setup(self):
        h = "aquilon91.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", PPROD, "--personality_stage", "next"]
        self.statustest(command)

    def test_601_justification_no_reason(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

    def test_605_update_personality_reason(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_610_add_parameter_reason(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test"] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_620_update_parameter_reason(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test"] + self.emergency_tcm_just_with_reason
        self.noouttest(command)

    def test_630_del_parameter_reason(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup"] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_640_map_grn_reason(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"] + self.emergency_tcm_just_with_reason
        self.noouttest(command)

    def test_650_map_grn_reason(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"] + self.emergency_tcm_just_with_reason
        self.noouttest(command)

    def test_660_add_required_svc_reason(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_670_del_required_svc_reason(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_675_add_required_svc_reason_os(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--osname", "linux", "--osversion",
                   "5.1-x86_64"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--osname", "linux", "--osversion",
                   "5.1-x86_64"] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_676_del_required_svc_reason_os(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--osname", "linux", "--osversion",
                   "5.1-x86_64"] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--osname", "linux", "--osversion",
                   "5.1-x86_64"] + self.emergency_tcm_just_with_reason
        self.noouttest(command)

    def test_680_add_static_route_reason(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD] + self.emergency_tcm_just_with_reason
        self.statustest(command)

    def test_690_del_static_route_reason(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD] + self.emergency_tcm_just_with_reason
        self.statustest(command)

    def test_700_add_service_reason(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_710_del_service_reason(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_720_add_feature_reason(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_730_del_feature_reason(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.emergency_just_with_reason
        self.emergencynojustification(command)

    def test_800_bind_feature_restricted(self):
        command = ["add", "feature", "--feature", "nonpublicfeature",
                   "--type", "host", "--grn", "grn:/ms/ei/aquilon/unittest",
                   "--activation", "reboot", "--deactivation", "reboot"]
        self.noouttest(command)

    def test_810_bind_feature_restricted_qa(self):
        command = ["bind", "feature", "--feature", "nonpublicfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.statustest(command)

        command = ["unbind", "feature", "--feature", "nonpublicfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        self.statustest(command)

    def test_820_bind_feature_restricted_prod(self):
        command = ["bind", "feature", "--feature", "nonpublicfeature",
                   "--archetype", "aquilon", "--personality", PPROD]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command = ["bind", "feature", "--feature", "nonpublicfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.valid_just_tcm
        self.statustest(command)

        command = ["unbind", "feature", "--feature", "nonpublicfeature",
                   "--archetype", "aquilon", "--personality", PPROD] + self.valid_just_tcm
        self.statustest(command)

    def test_850_bind_feature_restricted(self):
        command = ["del", "feature", "--feature", "nonpublicfeature",
                   "--type", "host"]
        self.noouttest(command)

    def test_860_accepted_tcm(self):
        # To Do: create tests for rejected tickets
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD] + self.valid_just_tcm
        self.noouttest(command)

    def test_870_accepted_sn(self):
        # To Do: create tests for rejected tickets
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD] + self.valid_just_sn
        self.noouttest(command)

    def test_880_bind_feature_prod_cluster(self):
        command = ["bind_feature", "--feature", "testclusterfeature",
                   "--personality", "hapersonality"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command += self.just_reason
        self.emergencynojustification(command)

    def test_890_add_parameter_definition_prod_cluster(self):
        command = ["add_parameter_definition", "--feature", "testclusterfeature",
                   "--type", "host", "--path=teststringcluster", "--value_type=string",
                   "--default", "default"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command += self.just_reason
        self.emergencynojustification(command)

    def test_895_del_parameter_definition_prod_cluster(self):
        command = ["del_parameter_definition", "--feature", "testclusterfeature",
                   "--type", "host", "--path=teststringcluster"]

        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command += self.just_reason
        self.emergencynojustification(command)

    def test_896_unbind_feature_prod_cluster(self):
        command = ["unbind_feature", "--feature", "testclusterfeature",
                   "--personality", "hapersonality"]
        self.justificationmissingtest(command, auth=True, msgcheck=False)

        command += self.emergency_just_without_reason
        self.reasonmissingtest(command, auth=True, msgcheck=False)

        command += self.just_reason
        self.emergencynojustification(command)


    def test_900_justification_required(self):
        command = "show host --host aquilon91.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, 'Environment: prod',
                         command)
        self.matchoutput(out, 'Build Status: ready',
                         command)
        command = ["add", "alias",
                   "--fqdn", "aliasjustreq.aqd-unittest.ms.com",
                   "--target", "aquilon91.aqd-unittest.ms.com"]
        self.justificationmissingtest_warn(command)
        command = ["add", "alias",
                   "--fqdn", "aliasjustreq2.aqd-unittest.ms.com",
                   "--target", "aliasjustreq.aqd-unittest.ms.com"]
        self.justificationmissingtest_warn(command)
        cmd = "show address --fqdn aquilon91.aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchoutput(out, "Aliases: aliasjustreq.aqd-unittest.ms.com, "
                              "aliasjustreq2.aqd-unittest.ms.com", cmd)

    def test_905_justification_required(self):
        command = ["del", "alias",
                   "--fqdn", "aliasjustreq2.aqd-unittest.ms.com"]
        self.justificationmissingtest_warn(command)
        command = ["del", "alias",
                   "--fqdn", "aliasjustreq.aqd-unittest.ms.com"] + self.valid_just_tcm
        self.successtest(command)
        cmd = "show address --fqdn aquilon91.aqd-unittest.ms.com"
        out = self.commandtest(cmd.split(" "))
        self.matchclean(out, "Aliases: aliasjustreq.aqd-unittest.ms.com, "
                             "aliasjustreq2.aqd-unittest.ms.com", cmd)

    def test_910_aqd_checkedm_unknownerror(self):
        command = ["update_domain", "--domain", "deployable", "--archived"]
        out = self.commandtest(command)
        command = ["del_domain", "--domain", "deployable"] + self.exception_trigger_just_tcm
        err = self.internalerrortest(command)
        self.matchoutput(err, "Invalid response received for the change management check. No JSON object could be decoded", command)
        command = ["update_domain", "--domain", "deployable", "--noarchived"]
        out = self.commandtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJustification)
    unittest.TextTestRunner(verbosity=2).run(suite)
