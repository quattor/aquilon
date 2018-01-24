#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Module for testing the search application, filesystem, hostlink, intervention,
 reboot_schedule, resourcegroup, service_address commands."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestSearchResource(TestBrokerCommand):

    def test_000_search_application(self):
        command = ['search_application', '--hostname', 'server1.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, 'Application: app1', command)
        self.matchoutput(out, 'Comments: Some application comments', command)

    def test_005_search_application_name(self):
        command = ['search_application', '--application', 'app1']
        out = self.commandtest(command)
        self.matchoutput(out, 'Application: app1', command)
        self.matchoutput(out, 'Comments: Some application comments', command)
        self.matchoutput(out, 'Bound to: Host server1.aqd-unittest.ms.com', command)

    def test_010_search_filesystem(self):
        command = ['search_filesystem', '--resourcegroup', 'utbvcs1cas01']
        out = self.commandtest(command)
        self.matchoutput(out, 'Filesystem: utbvcs1cas01', command)
        self.matchoutput(out, 'Bound to: Resource Group utbvcs1cas01', command)
        self.matchoutput(out, 'Block Device: /dev/vx/dsk/utbvcs1cas01.gnr.0/gnr.0', command)

    def test_015_search_filesystem_name(self):
        command = ['search_filesystem', '--filesystem', 'fs1']
        out = self.commandtest(command)
        self.matchoutput(out, 'Filesystem: fs1', command)
        self.matchoutput(out, 'Bound to: Resource Group utvcs1as1', command)
        self.matchoutput(out, 'Block Device: /dev/vx/dsk/dg.0/gnr.0', command)
        self.matchoutput(out, 'Bound to: Host server1.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Block Device: /dev/vx/dsk/dg.0/gnr.0', command)

    def test_020_search_hostlink(self):
        command = ['search_hostlink', '--hostname', 'server1.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, 'Hostlink: app1', command)
        self.matchoutput(out, 'Hostlink: app2', command)
        self.matchoutput(out, 'Hostlink: camelcase', command)

    def test_025_search_hostlink_name(self):
        command = ['search_hostlink', '--hostlink', 'camelcase']
        out = self.commandtest(command)
        self.matchoutput(out, 'Hostlink: camelcase', command)
        self.matchoutput(out, 'Bound to: Host server1.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Target Path: /var/spool/hostlinks/CaMeLcAsE', command)

    def test_030_search_intervention(self):
        command = ['search_intervention', '--hostname', 'server1.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, 'Intervention: i1', command)
        self.matchoutput(out, 'Intervention: blank', command)
        self.matchoutput(out, 'Intervention: groups', command)
        self.matchoutput(out, 'Intervention: disable', command)
        self.matchoutput(out, 'RebootIntervention', command)

    def test_035_search_intervention_name(self):
        command = ['search_intervention', '--intervention', 'disable']
        out = self.commandtest(command)
        self.matchoutput(out, 'Intervention: disable', command)
        self.matchoutput(out, 'Bound to: Host server1.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Reason: no-good-reason', command)

    def test_040_search_reboot_schedule(self):
        command = ['search_reboot_schedule', '--hostname', 'server2.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, 'RebootSchedule', command)
        self.matchoutput(out, 'Bound to: Host server2.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Week: 1,3', command)
        self.matchoutput(out, 'Day: Sat', command)
        self.matchoutput(out, 'Time: None', command)

    def test_045_search_resourcegroup(self):
        command = ['search_resourcegroup', '--cluster', 'utbvcs1c']
        out = self.commandtest(command)
        self.matchoutput(out, 'Resource Group: utbvcs1cas01', command)
        self.matchoutput(out, 'Bound to: High Availability Cluster utbvcs1c', command)
        self.matchoutput(out, 'Filesystem: utbvcs1cas01', command)
        self.matchoutput(out, 'Resource Group: utbvcs1cas02', command)
        self.matchoutput(out, 'Bound to: High Availability Cluster utbvcs1c', command)
        self.matchoutput(out, 'Filesystem: utbvcs1cas02', command)

    def test_050_search_resourcegroup_name(self):
        command = ['search_resourcegroup', '--resourcegroup', 'utbvcs4eas01']
        out = self.commandtest(command)
        self.matchoutput(out, 'Resource Group: utbvcs4eas01', command)
        self.matchoutput(out, 'Bound to: High Availability Cluster utbvcs4e', command)
        self.matchoutput(out, 'Filesystem: utbvcs4eas01', command)

    def test_055_service_address(self):
        command = ['search_service_address', '--hostname', 'unittest20.aqd-unittest.ms.com']
        out = self.commandtest(command)
        self.matchoutput(out, 'Service Address: hostname', command)
        self.matchoutput(out, 'Bound to: Host unittest20.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Service Address: zebra2', command)
        self.matchoutput(out, 'Bound to: Host unittest20.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Service Address: zebra3', command)
        self.matchoutput(out, 'Bound to: Host unittest20.aqd-unittest.ms.com', command)
        self.matchoutput(out, 'Service Address: et-unittest20', command)
        self.matchoutput(out, 'Bound to: Host unittest20.aqd-unittest.ms.com', command)

    def test_060_search_service_address_name(self):
        command = ['search_service_address', '--name', 'hostname']
        out = self.commandtest(command)
        self.matchoutput(out, 'Address: unittest20.aqd-unittest.ms.com [4.2.12.135]', command)
        self.matchoutput(out, 'Address: infra1.aqd-unittest.ms.com [4.2.12.133]', command)
        self.matchoutput(out, 'Address: infra2.aqd-unittest.ms.com [4.2.12.134]', command)
        self.matchoutput(out, 'Address: infra1.one-nyp.ms.com [4.2.12.197]', command)
        self.matchoutput(out, 'Address: infra2.one-nyp.ms.com [4.2.12.198]', command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchResource)
    unittest.TextTestRunner(verbosity=2).run(suite)