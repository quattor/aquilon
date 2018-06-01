#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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
"""Module for testing the add chassis command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from chassistest import VerifyChassisMixin


class TestAddChassis(TestBrokerCommand, VerifyChassisMixin):
    def test_100_add_ut3c5(self):
        command = ["add", "chassis", "--chassis", "ut3c5.aqd-unittest.ms.com",
                   "--rack", "np3", "--model", "utchassis",
                   "--serial", "ABC1234", "--comments", "Some chassis comments"]
        self.noouttest(command)

    def test_105_verify_ut3c5(self):
        self.verifychassis("ut3c5.aqd-unittest.ms.com", "aurora_vendor",
                           "utchassis", "np3", "a", "3", "ABC1234",
                           comments="Some chassis comments",
                           grn="grn:/ms/ei/aquilon/aqd")

    def test_106_show_ut3c5_proto(self):
        command = ["show", "chassis", "--chassis", "ut3c5.aqd-unittest.ms.com",
                   "--format", "proto"]
        chassis = self.protobuftest(command, expect=1)[0]

        self.assertEqual(chassis.name, 'ut3c5')
        self.assertEqual(chassis.primary_name, 'ut3c5.aqd-unittest.ms.com')
        self.assertEqual(chassis.serial_no, 'ABC1234')

        self.assertEqual(chassis.model.model_type, 'chassis')
        self.assertEqual(chassis.model.name, 'utchassis')
        self.assertEqual(chassis.model.vendor, 'aurora_vendor')

        self.assertEqual(chassis.location.location_type, 'rack')
        self.assertEqual(chassis.location.name, 'np3')
        self.assertEqual(chassis.location.fullname, 'np3')
        self.assertEqual(chassis.location.col, '3')
        self.assertEqual(chassis.location.row, 'a')

        self.assertEqual(len(chassis.slots), 0)

        self.assertEqual(len(chassis.interfaces), 1)

    def test_110_add_ut3c1(self):
        command = "add_chassis --chassis ut3c1.aqd-unittest.ms.com --rack ut3 --model aurora_chassis_model"
        self.noouttest(command.split(" "))

    def test_115_verify_ut3c1(self):
        self.verifychassis("ut3c1.aqd-unittest.ms.com",
                           "aurora_vendor", "aurora_chassis_model", "ut3", "a", "3")

    def test_116_add_ut3c1(self):
        command = "update_chassis --chassis ut3c1.aqd-unittest.ms.com --model utchassis"
        self.noouttest(command.split(" "))

    def test_117_verify_ut3c1(self):
        self.verifychassis("ut3c1.aqd-unittest.ms.com",
                           "aurora_vendor", "utchassis", "ut3", "a", "3")

    def test_118_verify_chassis_dns(self):
        command = "search_dns --fqdn ut3c1.aqd-unittest.ms.com"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)

    def test_120_add_ut9_chassis(self):
        for i in range(1, 8):
            ip = self.net["ut9_chassis"].usable[i]
            self.dsdb_expect_add("ut9c%d.aqd-unittest.ms.com" % i,
                                 ip, "oa", ip.mac)
            command = ["add", "chassis",
                       "--chassis", "ut9c%d.aqd-unittest.ms.com" % i,
                       "--rack", "ut9", "--model", "c-class",
                       "--ip", ip, "--mac", ip.mac, "--interface", "oa"]
            self.noouttest(command)
        self.dsdb_verify()

    def test_125_verify_ut9_chassis(self):
        for i in range(1, 6):
            self.verifychassis("ut9c%d.aqd-unittest.ms.com" % i,
                               "hp", "c-class", "ut9", "", "",
                               ip=str(self.net["ut9_chassis"].usable[i]),
                               mac=self.net["ut9_chassis"].usable[i].mac,
                               interface="oa")

    def test_130_add_np3c5(self):
        self.noouttest(["add_chassis", "--chassis", "np3c5.one-nyp.ms.com",
                        "--rack", "np3", "--model", "utchassis"])

    def test_200_reject_bad_label_implicit(self):
        command = ["add", "chassis", "--chassis", "not-alnum.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "utchassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Could not deduce a valid hardware label",
                         command)

    def test_200_reject_bad_label_explicit(self):
        command = ["add", "chassis", "--chassis", "ut3c6.aqd-unittest.ms.com",
                   "--label", "not-alnum", "--rack", "ut3", "--model", "utchassis"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Illegal hardware label format 'not-alnum'.",
                         command)

    def test_300_verifychassisall(self):
        command = ["show", "chassis", "--all"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "ut9c1.aqd-unittest.ms.com", command)

    def test_305_show_chassis_all_proto(self):
        command = ["show", "chassis", "--all", "--format", "proto"]
        chassis_list = self.protobuftest(command, expect=10)

        # Verify that the chassis that were created in the previous
        # methods of this class are in the protobuf dump too
        search_chassis_primary_name = set([
            'ut3c5.aqd-unittest.ms.com',
            'ut3c1.aqd-unittest.ms.com',
            'ut9c1.aqd-unittest.ms.com',
        ])
        for chassis in chassis_list:
            search_chassis_primary_name.discard(chassis.primary_name)

        self.assertFalse(
            search_chassis_primary_name,
            'The following chassis have not been found in the protobuf '
            'output: {}'.format(', '.join(search_chassis_primary_name)))

    def test_400_add_chassis_grn(self):
        command = ["add_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "utchassis",
                   "--grn", "grn:/ms/ei/aquilon/ut2"]
        self.noouttest(command)

    def test_410_verify_add_chassis_grn(self):
        command = ["show_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Primary Name: ut3c6.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/ut2", command)

    def test_420_del_chassis_grn(self):
        command = ["del_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com"]
        self.noouttest(command)

    def test_430_add_chassis_eon_id(self):
        command = ["add_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com",
                   "--rack", "ut3", "--model", "utchassis",
                   "--eon_id", "3"]
        self.noouttest(command)

    def test_440_verify_add_chassis_eon_id(self):
        command = ["show_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Primary Name: ut3c6.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Owned by GRN: grn:/ms/ei/aquilon/unittest",
                         command)

    def test_450_verify_add_chassis_eon_id_proto(self):
        command = ["show_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com",
                   "--format", "proto"]
        chassis_list = self.protobuftest(command, expect=1)
        chassis = chassis_list[0]

        self.assertEqual(chassis.owner_eonid, 3)

    def test_460_del_chassis_eon_id(self):
        command = ["del_chassis", "--chassis", "ut3c6.aqd-unittest.ms.com"]
        self.noouttest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddChassis)
    unittest.TextTestRunner(verbosity=2).run(suite)
