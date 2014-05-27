#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


class TestJustification(PersonalityTestMixin,
                         TestBrokerCommand):
    def test_100_setup(self):
        personalities = {
            'justify-qa': {'grn': GRN,
                             'environment': 'qa'},
            'justify-prod': {'grn': GRN,
                             'environment': 'prod'},
        }
        for personality, kwargs in personalities.items():
            self.create_personality("aquilon", personality, **kwargs)

        command = ["add", "feature", "--feature", "testfeature",
                   "--type", "host", "--comment", "Test comment"]
        self.noouttest(command)

    def test_200_reconfigure_personality(self):
        h = "aquilon91.aqd-unittest.ms.com"
        p = "justify-prod"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", p]
        out = self.successtest (command)

        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_210_add_parameter(self):
        p = "justify-prod"

        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_215_update_parameter(self):
        p = "justify-prod"

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_220_del_parameter(self):
        p = "justify-prod"

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_230_map_grn(self):
        p = "justify-prod"

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_240_unmap_grn(self):
        p = "justify-prod"

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp",
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_270_add_required_svc(self):
        p = "justify-prod"

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_280_del_required_svc(self):
        p = "justify-prod"

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_290_add_static_route(self):
        p = "justify-prod"

        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_300_del_static_route(self):
        p = "justify-prod"

        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_310_map_service(self):
        p = "justify-prod"

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_320_unmap_service(self):
        p = "justify-prod"

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_330_bind_feature(self):
        p = "justify-prod"

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_340_unbind_feature(self):
        p = "justify-prod"

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p]
        out = self.unauthorizedtest(command, auth=True, msgcheck=False)
        self.matchoutput(out, "Personality aquilon/%s is marked production "
                              "and is under change management control. Please specify --justification." % p,
                         command)

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p,
                   "--justification", "tcm=12345678"]
        out = self.successtest (command)

    def test_400_reconfigure_personality(self):
        h = "aquilon91.aqd-unittest.ms.com"
        p = "justify-qa"

        command = ["reconfigure", "--hostname", h,
                   "--archetype", "aquilon",
                   "--personality", p]
        out = self.successtest (command)

        command = ["update_personality",
                   "--archetype", "aquilon",
                   "--personality", p]
        out = self.successtest(command)

    def test_410_add_parameter(self):
        p = "justify-qa"

        command = ["add_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.successtest (command)

    def test_415_update_parameter(self):
        p = "justify-qa"

        command = ["update_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users",
                   "--value", "test"]
        out = self.successtest (command)

    def test_420_del_parameter(self):
        p = "justify-qa"

        command = ["del_parameter",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--path", "access/users"]
        out = self.successtest (command)

    def test_430_map_grn(self):
        p = "justify-qa"

        command = ["map_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.successtest (command)

    def test_440_unmap_grn(self):
        p = "justify-qa"

        command = ["unmap_grn",
                   "--archetype", "aquilon",
                   "--personality", p,
                   "--grn", GRN,
                   "--target", "esp"]
        out = self.successtest (command)

    def test_470_add_required_svc(self):
        p = "justify-qa"

        command = ["add_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p]
        out = self.successtest (command)

    def test_480_del_required_svc(self):
        p = "justify-qa"

        command = ["del_required_service", "--service=chooser1",
                   "--archetype=aquilon", "--personality", p]
        out = self.successtest (command)

    def test_490_add_static_route(self):
        p = "justify-qa"

        gw = self.net["routing1"].usable[-1]
        command = ["add", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p]
        out = self.successtest (command)

    def test_500_del_static_route(self):
        p = "justify-qa"

        gw = self.net["routing1"].usable[-1]
        command = ["del", "static", "route", "--gateway", gw,
                   "--ip", "192.168.248.0", "--prefixlen", "24",
                   "--personality", p]
        out = self.successtest (command)

    def test_510_map_service(self):
        p = "justify-prod"

        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p]
        out = self.successtest (command)

    def test_520_unmap_service(self):
        p = "justify-prod"

        command = ["unmap", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "aquilon", "--personality", p]
        out = self.successtest (command)

    def test_530_bind_feature(self):
        p = "justify-qa"

        command = ["bind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p]
        out = self.successtest (command)

    def test_540_unbind_feature(self):
        p = "justify-qa"

        command = ["unbind", "feature", "--feature", "testfeature",
                   "--archetype", "aquilon", "--personality", p]
        out = self.successtest (command)

    def test_600_cleanup(self):
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
