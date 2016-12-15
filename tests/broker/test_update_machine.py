#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
'Module for testing the update machine command.'

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand
from eventstest import EventsTestMixin
from eventstest import EventsTestMixin


class TestUpdateMachine(EventsTestMixin, TestBrokerCommand):
    def test_1000_update_ut3c1n3(self):
        self.event_upd_hardware('ut3c1n3')
        self.noouttest(["update", "machine", "--machine", "ut3c1n3",
                        "--slot", "10", "--serial", "USN99C5553",
                        "--uuid", "097a2277-840d-4bd5-8327-cf133aa3c9d3"])
        self.events_verify()

    def test_1005_show_ut3c1n3(self):
        command = "show machine --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n3", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut3c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 10", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853", command)
        self.matchoutput(out, "Cpu: e5-2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: USN99C5553", command)
        self.matchoutput(out, "UUID: 097a2277-840d-4bd5-8327-cf133aa3c9d3",
                         command)

    def test_1005_cat_ut3c1n3(self):
        command = "cat --machine ut3c1n3"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "USN99C5553";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/e5-2660"\),\s*'
                          r'create\("hardware/cpu/intel/e5-2660"\s*\)\s*\);',
                          command)
        self.matchoutput(out, '"chassis" = "ut3c1.aqd-unittest.ms.com";', command)
        self.matchoutput(out, '"slot" = 10;', command)
        self.matchoutput(out,
                         '"uuid" = "097a2277-840d-4bd5-8327-cf133aa3c9d3";',
                         command)

    def test_1006_clear_uuid(self):
        self.event_upd_hardware('ut3c1n3')
        command = ["update_machine", "--machine", "ut3c1n3", "--clear_uuid"]
        self.noouttest(command)
        self.events_verify()

    def test_1007_verify_no_uuid(self):
        command = ["show_machine", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.matchclean(out, "UUID", command)

        command = ["cat", "--machine", "ut3c1n3"]
        out = self.commandtest(command)
        self.matchclean(out, "uuid", command)

    def test_1010_update_ut3c5n10(self):
        self.event_upd_hardware('ut3c5n10')
        self.noouttest(["update", "machine",
                        "--hostname", "unittest02.one-nyp.ms.com",
                        "--chassis", "ut3c5.aqd-unittest.ms.com", "--slot", "20",
                        "--comments", "New machine comments"])
        self.events_verify()

    def test_1015_search_slot(self):
        command = "search machine --slot 20 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_1015_search_chassis_slot(self):
        command = "search machine --chassis ut3c5.aqd-unittest.ms.com --slot 20 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_1015_show_ut3c5n10(self):
        command = "show machine --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut3c5.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 20", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853", command)
        self.matchoutput(out, "Cpu: e5-2660 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: 99C5553", command)
        self.searchoutput(out, "^  Comments: New machine comments", command)

    def test_1015_cat_ut3c5n10(self):
        command = "cat --machine ut3c5n10"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "99C5553";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/e5-2660"\),\s*'
                          r'create\("hardware/cpu/intel/e5-2660"\s*\)\s*\);',
                          command)
        self.matchoutput(out, '"chassis" = "ut3c5.aqd-unittest.ms.com";', command)
        self.matchoutput(out, '"slot" = 20;', command)

    def test_1016_clear_comments(self):
        self.event_upd_hardware('ut3c5n10')
        self.noouttest(["update_machine", "--machine", "ut3c5n10", "--comments", ""])
        self.events_verify()

    def test_1017_verify_comments(self):
        command = ["show_machine", "--machine", "ut3c5n10"]
        out = self.commandtest(command)
        self.searchclean(out, "^  Comments", command)

    def test_1020_update_ut3c1n4_serial(self):
        self.event_upd_hardware('ut3c1n4')
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
                        "--serial", "USNKPDZ407"])
        self.events_verify()

    def test_1021_update_ut3c1n4_cpu(self):
        self.event_upd_hardware('ut3c1n4')
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
                        "--cpuname", "e5-2697-v3"])
        self.events_verify()

    def test_1022_update_ut3c1n4_rack(self):
        # Changing the rack will change the location of the plenary, so we
        # can test if the host profile gets written
        self.event_upd_hardware('ut3c1n4')
        self.noouttest(["update", "machine", "--machine", "ut3c1n4",
                        "--rack", "ut4"])
        self.events_verify()

    def test_1025_show_ut3c1n4(self):
        command = "show machine --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3c1n4", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Rack: ut4", command)
        self.matchoutput(out, "Vendor: ibm Model: hs21-8853", command)
        self.matchoutput(out, "Cpu: e5-2697-v3 x 2", command)
        self.matchoutput(out, "Memory: 8192 MB", command)
        self.matchoutput(out, "Serial: USNKPDZ407", command)

    def test_1025_cat_ut3c1n4(self):
        command = "cat --machine ut3c1n4"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out, '"serialnumber" = "USNKPDZ407";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/ibm/hs21-8853" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 8192\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/e5-2697-v3"\),\s*'
                          r'create\("hardware/cpu/intel/e5-2697-v3"\s*\)\s*\);',
                          command)

    def test_1025_cat_unittest01(self):
        # There should be no host template present after the update_machine
        # command
        command = ["cat", "--hostname", "unittest01.one-nyp.ms.com"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "not found", command)

    def test_1030_clearchassis(self):
        self.event_upd_hardware('ut9s03p1')
        command = ["update", "machine", "--machine", "ut9s03p1",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "1"]
        self.noouttest(command)
        self.events_verify()
        self.event_upd_hardware('ut9s03p1')
        command = ["update", "machine", "--machine", "ut9s03p1",
                   "--clearchassis"]
        self.noouttest(command)
        self.events_verify()

    def test_1031_verify_clearchassis(self):
        command = ["show", "machine", "--machine", "ut9s03p1"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p1", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)

    def test_1032_clearchassis_plus_new(self):
        self.event_upd_hardware('ut9s03p2')
        command = ["update", "machine", "--machine", "ut9s03p2",
                   "--chassis", "ut9c5.aqd-unittest.ms.com", "--slot", "1"]
        self.noouttest(command)
        self.events_verify()
        self.event_upd_hardware('ut9s03p2')
        command = ["update", "machine", "--machine", "ut9s03p2",
                   "--clearchassis",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "2"]
        self.noouttest(command)
        self.events_verify()

    def test_1033_verify_clearchassis_plus_new(self):
        command = ["show", "machine", "--machine", "ut9s03p2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p2", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 2", command)

    def test_1034_true_chassis_update(self):
        self.event_upd_hardware('ut9s03p3')
        command = ["update", "machine", "--machine", "ut9s03p3",
                   "--chassis", "ut9c5.aqd-unittest.ms.com", "--slot", "2"]
        self.noouttest(command)
        self.events_verify()
        self.event_upd_hardware('ut9s03p3')
        command = ["update", "machine", "--machine", "ut9s03p3",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "3"]
        self.noouttest(command)
        self.events_verify()

    def test_1035_verify_true_chassis_update(self):
        command = ["show", "machine", "--machine", "ut9s03p3"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p3", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 3", command)

    def test_1040_simple_chassis_update(self):
        self.event_upd_hardware('ut9s03p4')
        command = ["update", "machine", "--machine", "ut9s03p4",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "4"]
        self.noouttest(command)
        self.events_verify()

    def test_1041_verify_simple_chassis_update(self):
        command = ["show", "machine", "--machine", "ut9s03p4"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p4", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 4", command)

    def test_1042_simple_chassis_update2(self):
        command = ["update", "machine", "--machine", "ut9s03p5",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "5"]
        self.event_upd_hardware('ut9s03p5')
        self.noouttest(command)
        self.events_verify()

    def test_1043_verify_simple_chassis_update2(self):
        command = ["show", "machine", "--machine", "ut9s03p5"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p5", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 5", command)

    def test_1044_simple_chassis_update3(self):
        command = ["update", "machine", "--machine", "ut9s03p6",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "6"]
        self.event_upd_hardware('ut9s03p6')
        self.noouttest(command)
        self.events_verify()

    def test_1045_verify_simple_chassis_update3(self):
        command = ["show", "machine", "--machine", "ut9s03p6"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p6", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 6", command)

    def test_1050_different_rack(self):
        command = ["update", "machine", "--machine", "ut9s03p9",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "9"]
        self.event_upd_hardware('ut9s03p9')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p9",
                   "--rack", "ut8"]
        self.event_upd_hardware('ut9s03p9')
        self.noouttest(command)
        self.events_verify()

    def test_1055_verify_different_rack(self):
        command = ["show", "machine", "--machine", "ut9s03p9"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p9", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_1060_reuse_slot(self):
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "10"]
        self.event_upd_hardware('ut9s03p10')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--clearchassis"]
        self.event_upd_hardware('ut9s03p10')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p10",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "10"]
        self.event_upd_hardware('ut9s03p10')
        self.noouttest(command)
        self.events_verify()

    def test_1065_verify_reuse_slot(self):
        command = ["show", "machine", "--machine", "ut9s03p10"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p10", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 10", command)

    def test_1070_taken_slot(self):
        command = ["update", "machine", "--machine", "ut9s03p11",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "11"]
        self.event_upd_hardware('ut9s03p11')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p12",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "11"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Chassis ut9c1.aqd-unittest.ms.com slot 11 "
                              "already has machine ut9s03p11", command)

    def test_1075_verify_taken_slot(self):
        command = ["show", "machine", "--machine", "ut9s03p11"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p11", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c1.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 11", command)
        command = ["show", "machine", "--machine", "ut9s03p12"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p12", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def test_1080_multislot_clear(self):
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "13"]
        self.event_upd_hardware('ut9s03p13')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--multislot",
                   "--chassis", "ut9c1.aqd-unittest.ms.com", "--slot", "14"]
        self.event_upd_hardware('ut9s03p13')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p13",
                   "--clearchassis"]
        self.event_upd_hardware('ut9s03p13')
        self.noouttest(command)
        self.events_verify()

    def test_1085_verify_multislot_clear(self):
        command = ["show", "machine", "--machine", "ut9s03p13"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p13", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def test_1090_multislot_add(self):
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "1"]
        self.event_upd_hardware('ut9s03p15')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "2"]
        self.event_upd_hardware('ut9s03p15')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p15",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "3"]
        self.event_upd_hardware('ut9s03p15')
        self.noouttest(command)
        self.events_verify()

    def test_1095_verify_multislot_add(self):
        command = ["show", "machine", "--machine", "ut9s03p15"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p15", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 1", command)
        self.matchoutput(out, "Slot: 2", command)
        self.matchoutput(out, "Slot: 3", command)

    def test_1100_multislot_update_fail(self):
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "4"]
        self.event_upd_hardware('ut9s03p19')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--multislot",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "5"]
        self.event_upd_hardware('ut9s03p19')
        self.noouttest(command)
        self.events_verify()
        command = ["update", "machine", "--machine", "ut9s03p19",
                   "--chassis", "ut9c2.aqd-unittest.ms.com", "--slot", "6"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Use --multislot to support a machine in more "
                              "than one slot", command)

    def test_1105_verify_multislot_update_fail(self):
        command = ["show", "machine", "--machine", "ut9s03p19"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p19", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchoutput(out, "Chassis: ut9c2.aqd-unittest.ms.com", command)
        self.matchoutput(out, "Slot: 4", command)
        self.matchoutput(out, "Slot: 5", command)
        self.matchclean(out, "Slot: 6", command)

    def test_1110_move_machine_with_vms(self):
        old_path = ["machine", "americas", "ut", "ut3", "ut14s1p2"]
        new_path = ["machine", "americas", "ut", "ut14", "ut14s1p2"]

        self.check_plenary_exists(*old_path)
        self.check_plenary_gone(*new_path)
        self.event_upd_hardware('ut14s1p2')
        self.noouttest(["update", "machine", "--machine", "ut14s1p2",
                        "--rack", "ut14"])
        self.events_verify()
        self.check_plenary_gone(*old_path)
        self.check_plenary_exists(*new_path)

    def test_1115_show_ut14s1p2(self):
        command = ["show", "machine", "--machine", "ut14s1p2"]
        out = self.commandtest(command)
        self.matchoutput(out, "Rack: ut14", command)

    def test_1115_check_vm_location(self):
        for i in range(0, 3):
            machine = "evm%d" % (i + 50)
            command = ["show", "machine", "--machine", machine]
            out = self.commandtest(command)
            self.matchoutput(out, "Rack: ut14", command)

    def test_1120_update_ut3s01p2(self):
        self.event_upd_hardware('ut3s01p2')
        self.noouttest(["update", "machine", "--machine", "ut3s01p2",
                        "--model", "hs21-8853", "--vendor", "ibm"])
        self.events_verify()

    def test_1125_show_ut3s01p2(self):
        command = "show machine --machine ut3s01p2"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p2", command)
        self.matchoutput(out, "Model Type: blade", command)

    def test_1130_verify_initial_state(self):
        command = "cat --machine evm1"
        out = self.commandtest(command.split(" "))
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/utvirt/default",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "00:50:56:01:20:00"\s*\);',
                          command)

    def test_1131_update_default_nic_model(self):
        command = ["update_machine", "--machine=evm1", "--model=utlarge",
                   "--cpucount=2", "--memory=12288"]
        self.event_upd_hardware('evm1')
        self.noouttest(command)
        self.events_verify()

    def test_1132_cat_evm1(self):
        command = "cat --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, '"location" = "ut.ny.na";', command)
        self.matchoutput(out,
                         'include { "hardware/machine/utvendor/utlarge" };',
                         command)
        self.searchoutput(out,
                          r'"ram" = list\(\s*'
                          r'create\("hardware/ram/generic",\s*'
                          r'"size", 12288\*MB\s*\)\s*\);',
                          command)
        self.searchoutput(out,
                          r'"cpu" = list\(\s*'
                          r'create\("hardware/cpu/intel/l5520"\),\s*'
                          r'create\("hardware/cpu/intel/l5520"\)\s*\);',
                          command)
        # Updating the model of the machine changes the NIC model from
        # utvirt/default to generic/generic_nic
        self.searchoutput(out,
                          r'"cards/nic/eth0" = '
                          r'create\("hardware/nic/generic/generic_nic",\s*'
                          r'"boot", true,\s*'
                          r'"hwaddr", "00:50:56:01:20:00"\s*\);',
                          command)

    def test_1132_show_evm1(self):
        command = "show machine --machine evm1"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: evm1", command)
        self.matchoutput(out, "Model Type: virtual_machine", command)
        self.matchoutput(out, "Hosted by: ESX Cluster utecl1", command)
        self.matchoutput(out, "Building: ut", command)
        self.matchoutput(out, "Vendor: utvendor Model: utlarge", command)
        self.matchoutput(out, "Cpu: l5520 x 2", command)
        self.matchoutput(out, "Memory: 12288 MB", command)
        self.searchoutput(out,
                          r"Interface: eth0 00:50:56:01:20:00 \[boot, default_route\]\s*"
                          r"Type: public\s*"
                          r"Vendor: generic Model: generic_nic$",
                          command)

    def test_1135_restore_status_quo(self):
        self.event_upd_hardware('evm1')
        command = ["update_machine", "--machine=evm1", "--model=utmedium",
                   "--cpucount=1", "--memory=8192"]
        self.noouttest(command)
        self.events_verify()

    def test_2000_bad_cpu_vendor(self):
        self.notfoundtest(["update", "machine", "--machine", "ut3c1n4",
                           "--cpuvendor", "no-such-vendor"])

    def test_2000_bad_cpu_name(self):
        self.notfoundtest(["update", "machine", "--machine", "ut3c1n4",
                           "--cpuname", "no-such-cpu"])

    def test_2000_phys_to_cluster(self):
        command = ["update_machine", "--machine=ut9s03p19", "--cluster=utecl1"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Cannot convert a physical machine to virtual.",
                         command)

    def test_2000_steal_ip(self):
        ip = self.net["unknown0"].usable[2]
        command = ["update_machine", "--machine", "ut3c1n3", "--ip", ip]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "IP address %s is already in use by public interface "
                         "eth0 of machine unittest00.one-nyp.ms.com" % ip,
                         command)

    def test_2010_missing_slot(self):
        command = ["update", "machine", "--machine", "ut9s03p7",
                   "--chassis", "ut9c1.aqd-unittest.ms.com"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Option --chassis requires --slot information",
                         command)

    def test_2015_verify_missing_slot(self):
        command = ["show", "machine", "--machine", "ut9s03p7"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p7", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def test_2020_missing_chassis(self):
        command = ["update", "machine", "--machine", "ut9s03p8",
                   "--slot", "8"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "Option --slot requires --chassis information",
                         command)

    def test_2025_verify_missing_chassis(self):
        command = ["show", "machine", "--machine", "ut9s03p8"]
        out = self.commandtest(command)
        self.matchoutput(out, "Machine: ut9s03p8", command)
        self.matchoutput(out, "Model Type: blade", command)
        self.matchclean(out, "Chassis: ", command)
        self.matchclean(out, "Slot: ", command)

    def test_2030_reject_machine_uri(self):
        command = ["update", "machine", "--machine", "ut3c1n9",
                   "--uri", "file:///somepath/to/ovf"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "URI can be specified only for virtual "
                         "machines and the model's type is blade",
                         command)

    def test_2035_verify_reject_machine_uri(self):
        command = ["show", "machine", "--machine", "ut3c1n9"]
        out = self.commandtest(command)
        self.matchclean(out, "URI:", command)

    # These tests would be nice, but twisted just ignores the permission
    # on the files since we're still the owner.  Which is good, but means
    # the recovery routines can't be easily tested.
#   def testfailbrokenplenary(self):
#       template = self.plenary_name("machine", "americas", "ut", "ut9",
#                                    "ut9s03p20")
#       os.chmod(template, 0000)
#       command = ["update_machine", "--machine=ut9s03p20", "--serial=20"]
#       out = self.badrequesttest(command)
#       self.matchoutput(out, "FIXME", command)

#   def testverifyfailbrokenplenary(self):
#       # Fixing the previous breakage... not actually necessary for this test.
#       template = self.plenary_name("machine", "americas", "ut", "ut9",
#                                    "ut9s03p20")
#       os.chmod(template, 0644)
#       command = ["show_machine", "--machine=ut9s03p20"]
#       out = self.commandtest(command)
#       self.matchclean(out, "Serial", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestUpdateMachine)
    unittest.TextTestRunner(verbosity=2).run(suite)
