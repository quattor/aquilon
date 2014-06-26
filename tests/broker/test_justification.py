#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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

import os

if __name__ == "__main__":
    import utils
    utils.import_depends()


import unittest2 as unittest
from broker.brokertest import TestBrokerCommand
from broker.personalitytest import PersonalityTestMixin

GRN = "grn:/ms/ei/aquilon/aqd"
PPROD = "justify-prod"
QPROD = "justify-qa"
AUTHERR = "Personality aquilon/%s is marked production and is under change management control. Please specify --justification or --justification='emergency' and reason."
AUTHERR2 = "Justification of 'emergency' requires --reason to be specified."

class TestJustification(PersonalityTestMixin,
                         TestBrokerCommand):
    def test_100_setup(self):
        personalities = {
            QPROD: {'grn': GRN,
                    'environment': 'qa'},
            PPROD: {'grn': GRN,
                    'environment': 'prod'},
        }
        for personality, kwargs in personalities.items():
            self.create_personality("aquilon", personality, **kwargs)

        command = ["add", "feature", "--feature", "testfeature",
                   "--type", "host", "--comment", "Test comment"]
        self.noouttest(command)

    def test_110_host_setup(self):
        h = "aquilon91.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", PPROD]
        out = self.successtest (command)

    def test_200_update_personality(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_210_add_parameter(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_215_update_parameter(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--value", "test",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_220_del_parameter(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/users",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_230_map_grn(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_240_unmap_grn(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_270_add_required_svc(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_280_del_required_svc(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_290_add_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_300_del_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_310_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_320_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_330_bind_feature(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_340_unbind_feature(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR % PPROD, command )

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_400_host_setup(self):
        h = "aquilon91.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", QPROD]
        out = self.successtest (command)

    def test_405_update_personality(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", QPROD]
        out = self.successtest(command)

    def test_410_add_parameter(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.successtest (command)

    def test_415_update_parameter(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.successtest (command)

    def test_420_del_parameter(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--path", "access/users"]
        out = self.successtest (command)

    def test_430_map_grn(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.successtest (command)

    def test_440_unmap_grn(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", QPROD,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.successtest (command)

    def test_470_add_required_svc(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_480_del_required_svc(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_490_add_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", QPROD]
        out = self.successtest (command)

    def test_500_del_static_route(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", QPROD]
        out = self.successtest (command)

    def test_510_map_service(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_520_unmap_service(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_530_bind_feature(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_540_unbind_feature(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", QPROD]
        out = self.successtest (command)

    def test_600_host_setup(self):
        h = "aquilon91.aqd-unittest.ms.com"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", PPROD]
        out = self.successtest (command)

    def test_600_update_personality_reason(self):
        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_610_add_parameter_reason(self):
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test",
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )
         
        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test",
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_620_update_parameter_reason(self):
        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test",
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--value", "test",
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_630_del_parameter_reason(self):
        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--path", "access/netgroup",
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_640_map_grn_reason(self):
        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_650_map_grn_reason(self):
        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", PPROD,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_660_add_required_svc_reason(self):
        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_670_del_required_svc_reason(self):
        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_680_add_static_route_reason(self):
        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_690_del_static_route_reason(self):
        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_700_add_service_reason(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_710_del_service_reason(self):
        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_720_add_feature_reason(self):
        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_730_del_feature_reason(self):
        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out,  AUTHERR2, command )

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", PPROD,
                   "--justification", "emergency",
                   "--reason", "reason flag check"]
        out = self.successtest (command)

    def test_800_cleanup(self):
        h = "aquilon91.aqd-unittest.ms.com"
        p = "unixeng-test"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", p]
        out = self.successtest (command)

        command = ["del_personality", "--archetype", "aquilon",
                   "--personality", "justify-qa"]
        out = self.successtest (command)

        command = ["del_personality", "--archetype", "aquilon",
                   "--personality", "justify-prod"]
        out = self.successtest (command)

        command = ["del", "feature", "--feature", "testfeature",
                   "--type", "host"]
        self.noouttest(command)



if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestJustification)
    unittest.TextTestRunner(verbosity=2).run(suite)
