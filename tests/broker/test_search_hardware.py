#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Module for testing the search hardware command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand


class TestSearchHardware(TestBrokerCommand):

    def testmodelavailable(self):
        command = "search hardware --model hs21-8853l5u"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c1n3", command)
        self.matchoutput(out, "ut3c1n4", command)
        self.matchoutput(out, "ut3c5n10", command)

    def testmodelunavailable(self):
        command = "search hardware --model model-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model model-does-not-exist not found.",
                         command)

    def testmodelavailablefull(self):
        command = "search hardware --model poweredge_6650 --fullinfo"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Machine: ut3s01p1", command)

    def testmodelvendorconflict(self):
        command = "search hardware --model vb1205xm --vendor dell"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model vb1205xm, vendor dell not found.",
                         command)

    def testmodelmachinetypeconflict(self):
        command = ["search_hardware", "--model=vb1205xm",
                   "--machine_type=virtual_machine"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Model vb1205xm, model_type "
                         "virtual_machine not found.", command)

    def testvendoravailable(self):
        command = "search hardware --vendor verari"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut8s02p1", command)
        self.matchoutput(out, "ut8s02p2", command)
        self.matchoutput(out, "ut8s02p3", command)

    def testvendorunavailable(self):
        command = "search hardware --vendor vendor-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Vendor vendor-does-not-exist not found",
                         command)

    def testmachinetypeavailable(self):
        command = "search hardware --machine_type blade"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut8s02p1", command)

    def testmachinetypeunavailable(self):
        command = "search hardware --machine_type machine_type-does-not-exist"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Unknown machine type "
                         "machine_type-does-not-exist", command)

    def testserialavailable(self):
        command = "search hardware --serial 99C5553"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c5n10", command)

    def testserialunavailable(self):
        command = "search hardware --serial SERIALDOESNOTEXIST"
        self.noouttest(command.split(" "))

    def testmacavailable(self):
        command = "search hardware --mac " + self.net["unknown0"].usable[2].mac
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c1n3", command)

    def testmacunavailable(self):
        command = "search hardware --mac 02:02:c7:62:10:04"
        self.noouttest(command.split(" "))

    def testlocation(self):
        command = "search hardware --building np"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ny00l4as01", command)
        self.matchoutput(out, "evm70", command)
        self.matchoutput(out, "np3c5n5", command)
        self.matchoutput(out, "np06bals03", command)

    def testlocationexact(self):
        command = "search hardware --building np --exact_location"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ny00l4as01", command)
        self.matchclean(out, "evm70", command)
        self.matchclean(out, "np3c5n5", command)
        self.matchclean(out, "np06bals03", command)

    def testlocationunavailable(self):
        command = "search hardware --building building-does-not-exist"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "not found", command)

    def testall(self):
        command = "search hardware --all"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "ut3gd1r01", command)
        self.matchoutput(out, "ut3c1", command)
        self.matchoutput(out, "ut3s01p1", command)
        self.matchoutput(out, "ny00l4as01", command)

    def testallfull(self):
        command = "search hardware --all --fullinfo"
        out = self.commandtest(command.split(" "))
        # This is a good sampling, but not the full output
        self.matchoutput(out, "Switch: ut3gd1r01", command)
        self.matchoutput(out, "Chassis: ut3c1", command)
        self.matchoutput(out, "Machine: ut3c5n10", command)
        self.matchoutput(out, "Machine: ut3s01p1", command)
        self.matchoutput(out, "Machine: ny00l4as01", command)

    def testsearchinterfacemodel(self):
        command = ["search", "hardware", "--interface_model", "e1000"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c5n2", command)
        self.matchclean(out, "ut3c5n1", command)
        self.matchclean(out, "ut3c5n3", command)
        self.matchclean(out, "ut3gd1r01", command)

    def testsearchinterfacevendor(self):
        command = ["search", "hardware", "--interface_vendor", "intel"]
        out = self.commandtest(command)
        self.matchoutput(out, "ut3c5n2", command)
        self.matchclean(out, "ut3c5n1", command)
        self.matchclean(out, "ut3c5n3", command)
        self.matchclean(out, "ut3gd1r01", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestSearchHardware)
    unittest.TextTestRunner(verbosity=2).run(suite)
