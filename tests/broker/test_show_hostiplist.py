#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2012,2013  Contributor
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
"""Module for testing the show hostiplist command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestShowHostIPList(TestBrokerCommand):

    def testshowhostiplist(self):
        command = "show hostiplist"
        out = self.commandtest(command.split(" "))
        dynip = self.net["dyndhcp0"].usable[2]
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[0],
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[2],
                         command)
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net["unknown0"].usable[3],
                         command)
        self.matchoutput(out,
                         "unittest00r.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[4],
                         command)
        self.matchoutput(out,
                         "dynamic-%s.aqd-unittest.ms.com,%s,\n" %
                         (str(dynip).replace(".", "-"), dynip),
                         command)
        self.matchoutput(out,
                         "arecord13.aqd-unittest.ms.com,%s,\n" %
                         self.net["unknown0"].usable[13],
                         command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)

    def testshowhostiplistarchetype(self):
        command = "show hostiplist --archetype aquilon"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "unittest02.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[0],
                         command)
        self.matchoutput(out,
                         "unittest00.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[2],
                         command)
        self.matchoutput(out,
                         "unittest00-e1.one-nyp.ms.com,%s,"
                         "unittest00.one-nyp.ms.com" %
                         self.net["unknown0"].usable[3],
                         command)
        self.matchoutput(out,
                         "unittest00r.one-nyp.ms.com,%s,\n" %
                         self.net["unknown0"].usable[4],
                         command)
        self.matchoutput(out, "aquilon61.aqd-unittest.ms.com", command)
        self.matchclean(out, "dynamic-", command)
        self.matchclean(out, "arecord13.aqd-unittest.ms.com", command)
        self.matchclean(out, "unittest01.one-nyp.ms.com", command)
        self.matchclean(out, "evh1.aqd-unittest.ms.com", command)
        self.matchclean(out, "evh2.aqd-unittest.ms.com", command)
        self.matchclean(out, self.aurora_with_node, command)
        self.matchclean(out, self.aurora_without_node, command)
        self.matchclean(out, "nyaqd1", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestShowHostIPList)
    unittest.TextTestRunner(verbosity=2).run(suite)
