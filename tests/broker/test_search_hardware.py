#!/usr/bin/env python2.6
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Module for testing the search hardware command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

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
        self.matchoutput(out, "Rackmount: ut3s01p1", command)

    def testmodelvendorconflict(self):
        command = "search hardware --model vb1205xm --vendor dell"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model vb1205xm, vendor dell not found.",
                         command)

    def testmodelmachinetypeconflict(self):
        command = ["search_hardware", "--model=vb1205xm",
                   "--machine_type=virtual_machine"]
        out = self.notfoundtest(command)
        self.matchoutput(out, "Model vb1205xm, machine_type "
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
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "Model machine_type "
                         "machine_type-does-not-exist not found.", command)

    def testserialavailable(self):
        command = "search hardware --serial 99C5553"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c5n10", command)

    def testserialunavailable(self):
        command = "search hardware --serial SERIALDOESNOTEXIST"
        self.noouttest(command.split(" "))

    def testmacavailable(self):
        command = "search hardware --mac " + self.net.unknown[0].usable[2].mac
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ut3c1n3", command)

    def testmacunavailable(self):
        command = "search hardware --mac 02:02:c7:62:10:04"
        self.noouttest(command.split(" "))

    def testlocation(self):
        command = "search hardware --building np"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ny00l4as01", command)
        self.matchoutput(out, "np997gd1r04", command)

    def testlocationexact(self):
        command = "search hardware --building np --exact_location"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "ny00l4as01", command)
        self.matchclean(out, "np997gd1r04", command)

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
        self.matchoutput(out, "Blade: ut3c5n10", command)
        self.matchoutput(out, "Rackmount: ut3s01p1", command)
        self.matchoutput(out, "Aurora_node: ny00l4as01", command)

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

