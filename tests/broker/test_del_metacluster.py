#!/usr/bin/env python2.6
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
"""Module for testing the del metacluster command."""


import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand


class TestDelMetaCluster(TestBrokerCommand):

    def testdelutmc1(self):
        command = ["del_metacluster", "--metacluster=utmc1"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc1(self):
        command = ["show_metacluster", "--metacluster=utmc1"]
        self.notfoundtest(command)

    def testdelutmc2(self):
        command = ["del_metacluster", "--metacluster=utmc2"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc2(self):
        command = ["show_metacluster", "--metacluster=utmc2"]
        self.notfoundtest(command)

    def testdelutmc3(self):
        command = ["del_metacluster", "--metacluster=utmc3"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifydelutmc3(self):
        command = ["show_metacluster", "--metacluster=utmc3"]
        self.notfoundtest(command)

    def testdelutmc4(self):
        command = ["del_metacluster", "--metacluster=utmc4"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc5(self):
        command = ["del_metacluster", "--metacluster=utmc5"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc6(self):
        command = ["del_metacluster", "--metacluster=utmc6"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutmc7(self):
        command = ["del_metacluster", "--metacluster=utmc7"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelutsandbox(self):
        # Test moving machines between metaclusters
        command = ["del_metacluster", "--metacluster=sandboxmc"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testdelvulcan1(self):
        command = ["del_metacluster", "--metacluster=vulcan1"]
        err = self.statustest(command)
        self.matchoutput(err, "sent 0 server notifications", command)

    def testverifyall(self):
        command = ["show_metacluster", "--all"]
        out = self.commandtest(command)
        self.matchclean(out, "Metacluster: utmc", command)

    def testdelnotfound(self):
        command = ["del_metacluster",
                   "--metacluster=metacluster-does-not-exist"]
        self.notfoundtest(command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestDelMetaCluster)
    unittest.TextTestRunner(verbosity=2).run(suite)
