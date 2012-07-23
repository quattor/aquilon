#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2013  Contributor
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
"""Module for testing constraints in commands involving metaclusters."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestMetaClusterConstraints(TestBrokerCommand):

    def testdelmetaclusterwithclusters(self):
        command = "del metacluster --metacluster utmc1"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Metacluster utmc1 is still in use by clusters",
                         command)

    def testfailrebindmetacluster(self):
        command = ["rebind_metacluster", "--cluster=utecl1",
                   "--metacluster=utmc2"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Cannot move cluster to a new metacluster "
                         "while virtual machines are attached.",
                         command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(
        TestMetaClusterConstraints)
    unittest.TextTestRunner(verbosity=2).run(suite)
