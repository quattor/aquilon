#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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
"""Module for testing the add intervention command."""

from datetime import datetime, timedelta

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

when = datetime.utcnow().replace(microsecond=0) + timedelta(days=1)
EXPIRY = when.isoformat()
when = EXPIRY.replace("T", " ")


class TestAddIntervention(TestBrokerCommand):

    def test_00_bad_intervention_times(self):
        command = ["add_intervention", "--intervention=i1",
                   "--expiry=long long ago",
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowusers=njw",
                   "--comments=testing"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the expiry value 'long long ago' "
                         "could not be interpreted", command)

        command = ["add_intervention", "--intervention=i1",
                   "--expiry='%s'" % when,
                   "--start=long long ago",
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowusers=njw",
                   "--comments=testing"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the start time 'long long ago' "
                         "could not be interpreted", command)

        too_late = datetime.utcnow().replace(microsecond=0) + timedelta(days=2)
        too_late = too_late.isoformat().replace("T", " ")
        command = ["add_intervention", "--intervention=i1",
                   "--expiry='%s'" % when,
                   "--start='%s'" % too_late,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowusers=njw",
                   "--comments=testing"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "the start time is later than the expiry time",
                         command)

    def test_05_add_basic_intervention(self):
        command = ["add_intervention", "--intervention=i1",
                   "--expiry='%s'" % when,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowusers=njw",
                   "--comments=testing"]
        self.successtest(command)

        command = ["show_intervention", "--intervention=i1",
                   "--hostname=server1.aqd-unittest.ms.com"]

        out = self.commandtest(command)
        self.matchoutput(out, "Intervention: i1", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchoutput(out, "Expires: %s" % when, command)
        self.matchoutput(out, "Start:", command)
        self.matchoutput(out, "Allow Users: njw", command)
        self.matchoutput(out, "Justification: no-good-reason", command)
        self.matchoutput(out, "Comments: testing", command)

    def test_10_addexisting(self):
        command = ["add_intervention", "--intervention=i1",
                   "--expiry='%s'" % when,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowusers=njw",
                   "--comments=testing"]
        out = self.badrequesttest(command)
        self.matchoutput(out, "already exists", command)

    def test_10_intervention_varieties(self):
        command = ["add_intervention", "--intervention=blank",
                   "--expiry='%s'" % when,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--comments=testing"]
        self.successtest(command)

        lookfor = "group1,group2"
        command = ["add_intervention", "--intervention=groups",
                   "--expiry='%s'" % when,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--allowgroups=%s" % lookfor,
                   "--comments=testing"]
        self.successtest(command)

        command = ["add_intervention", "--intervention=disable",
                   "--expiry='%s'" % when,
                   "--justification=no-good-reason",
                   "--hostname=server1.aqd-unittest.ms.com",
                   "--disabled_actions=startup",
                   "--comments=testing"]
        self.successtest(command)

        command = ["show_intervention", "--intervention=blank",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Intervention: blank", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "Allow Users", command)
        self.matchclean(out, "Allow Groups", command)
        self.matchclean(out, "Disabled", command)

        command = ["show_intervention", "--intervention=groups",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Intervention: groups", command)
        self.matchoutput(out, "Bound to: Host server1.aqd-unittest.ms.com",
                         command)
        self.matchclean(out, "Allow Users", command)
        self.matchoutput(out, "Allow Groups: %s" % lookfor, command)
        self.matchclean(out, "Disabled Actions", command)

        command = ["show_intervention",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Intervention: i1", command)
        self.matchoutput(out, "Intervention: blank", command)
        self.matchoutput(out, "Intervention: groups", command)
        self.matchoutput(out, "Intervention: disable", command)

        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com",
                   "--format=proto"]
        out = self.commandtest(command)
        hostlist = self.parse_hostlist_msg(out, expect=1)
        host = hostlist.hosts[0]
        for resource in host.resources:
            if resource.name == "groups" and resource.type == "intervention":
                self.assertEqual(resource.ivdata.groups, lookfor,
                                 "intervention should be found "
                                 "in protobufs as '%s', but is '%s'" %
                                 (lookfor, resource.ivdata.groups))

    def test_15_notfoundfs(self):
        command = "show intervention --intervention id-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_20_catintervention(self):
        command = ["cat", "--intervention=i1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "structure template resource"
                         "/host/server1.aqd-unittest.ms.com"
                         "/intervention/i1/config;",
                         command)
        self.matchoutput(out, '"name" = "i1";', command)
        self.matchoutput(out, '"start" =', command)
        self.matchoutput(out, '"expiry" = "%s"' % EXPIRY, command)

    def test_25_compile(self):
        command = ["reconfigure", "--hostname=server1.aqd-unittest.ms.com"]
        # Just want to know that a compile with the new resource works.
        self.successtest(command)

    def test_30_checkhost(self):
        command = ["show_host", "--hostname=server1.aqd-unittest.ms.com"]
        out = self.commandtest(command)
        self.matchoutput(out, "Intervention: i1", command)

        command = ["cat", "--generate",
                   "--hostname=server1.aqd-unittest.ms.com", "--data"]
        out = self.commandtest(command)
        self.matchoutput(out, '"system/resources/intervention" = append(create("resource/host/server1.aqd-unittest.ms.com/intervention/i1/config"))',
                         command)

        command = ["del_intervention", "--intervention=i1",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_intervention", "--intervention=blank",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_intervention", "--intervention=groups",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

        command = ["del_intervention", "--intervention=disable",
                   "--hostname=server1.aqd-unittest.ms.com"]
        self.successtest(command)

    def test_35_compile(self):
        command = ["reconfigure", "--hostname=server1.aqd-unittest.ms.com"]
        # Generate a profile without interventions.
        self.successtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddIntervention)
    unittest.TextTestRunner(verbosity=2).run(suite)
