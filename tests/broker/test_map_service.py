#!/usr/bin/env python2.5
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Module for testing the map service command."""

import os
import sys
import unittest

if __name__ == "__main__":
    BINDIR = os.path.dirname(os.path.realpath(sys.argv[0]))
    SRCDIR = os.path.join(BINDIR, "..", "..")
    sys.path.append(os.path.join(SRCDIR, "lib", "python2.5"))

from brokertest import TestBrokerCommand


class TestMapService(TestBrokerCommand):

    def testmapafs(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "afs", "--instance", "q.ny.ms.com"])

    def testverifymapafs(self):
        command = "show map --service afs --instance q.ny.ms.com --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype: aquilon Service: afs "
                         "Instance: q.ny.ms.com Map: Building ut",
                         command)

    def testverifynomatch(self):
        command = "show map --service afs --instance q.ny.ms.com --organization ms"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "No matching map found.", command)

    def testmapdns(self):
        self.noouttest(["map", "service", "--hub", "ny",
                        "--service", "dns", "--instance", "nyinfratest"])

    def testverifymapdns(self):
        command = ["show", "map", "--hub", "ny",
                   "--service", "dns", "--instance", "nyinfratest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: nyinfratest Map: Hub ny",
                         command)

    def testmapaqd(self):
        self.noouttest(["map", "service", "--campus", "ny",
                        "--service", "aqd", "--instance", "ny-prod"])

    def testverifymapaqd(self):
        command = ["show_map",
                   "--service=aqd", "--instance=ny-prod", "--campus=ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: aqd "
                         "Instance: ny-prod Map: Campus ny",
                         command)

    def testmaplemon(self):
        self.noouttest(["map", "service", "--campus", "ny",
                        "--service", "lemon", "--instance", "ny-prod"])

    def testverifymaplemon(self):
        command = ["show_map",
                   "--service=lemon", "--instance=ny-prod", "--campus=ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: lemon "
                         "Instance: ny-prod Map: Campus ny",
                         command)

    def testmapbootserver(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "bootserver", "--instance", "np.test"])

    def testverifymapbootserver(self):
        command = ["show_map", "--service", "bootserver",
                   "--instance", "np.test", "--building", "ut"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: bootserver "
                         "Instance: np.test Map: Building ut",
                         command)

    def testmapntp(self):
        self.noouttest(["map", "service", "--city", "ny",
                        "--service", "ntp", "--instance", "pa.ny.na"])

    def testverifymapntp(self):
        command = ["show_map",
                   "--service=ntp", "--instance=pa.ny.na", "--city=ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: ntp "
                         "Instance: pa.ny.na Map: City ny",
                         command)

    def testmaputsi1(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi1"])

    def testmaputsi2(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi2"])

    def testverifymaputsvc(self):
        command = "show map --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi1 Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi2 Map: Building ut",
                         command)

    def testverifyutmapproto(self):
        command = "show map --building ut --format proto"
        out = self.commandtest(command.split(" "))
        self.parse_servicemap_msg(out)

    def testmapchooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for n in ['a', 'b', 'c']:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                instance = "ut.%s" % n
                self.noouttest(["map", "service", "--building", "ut",
                                "--service", service, "--instance", instance])

    def testmaputsilpersona(self):
        self.noouttest(["map", "service", "--organization", "ms",
                        "--service", "utsvc", "--instance", "utsi2",
                        "--archetype", "aquilon",
                        "--personality", "lemon-collector-oracle"])

    def testverifymappersona(self):
        command = ["show_map", "--archetype=aquilon",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Company ms",
                         command)

    def testverifymapwihtoutarchetype(self):
        command = ["show_map",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Company ms",
                         command)

    def testverifymapwihtoutpersonality(self):
        command = ["show_map", "--archetype=aquilon", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Company ms",
                         command)

    def testverifypersonalitymapproto(self):
        command = ["show_map", "--format=proto", "--archetype=aquilon",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        servicemaplist = self.parse_servicemap_msg(out, expect=1)
        map = servicemaplist.servicemaps[0]
        self.failUnlessEqual(map.location.name, 'ms')
        self.failUnlessEqual(map.location.location_type, 'company')
        self.failUnlessEqual(map.service.name, 'utsvc')
        self.failUnlessEqual(map.service.serviceinstances[0].name, 'utsi2')
        self.failUnlessEqual(map.personality.name, 'lemon-collector-oracle')
        self.failUnlessEqual(map.personality.archetype.name, 'aquilon')

    def testmapwindowsfail(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "windows"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)

    def testmapgenericfail(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--personality", "generic"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)

    def testmapesx(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "esx_management_server",
                        "--instance", "ut.a", "--archetype", "vmhost",
                        "--personality", "esx_server"])
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "esx_management_server",
                        "--instance", "ut.b", "--archetype", "vmhost",
                        "--personality", "esx_server"])
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "vmseasoning", "--instance", "salt",
                        "--archetype", "vmhost",
                        "--personality", "esx_server"])
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "vmseasoning", "--instance", "pepper",
                        "--archetype", "vmhost",
                        "--personality", "esx_server"])

    def testverifymapesx(self):
        command = ["show_map", "--archetype=vmhost",
                   "--personality=esx_server", "--building=ut"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: vmhost Personality: esx_server "
                         "Service: esx_management_server Instance: ut.a "
                         "Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: vmhost Personality: esx_server "
                         "Service: esx_management_server Instance: ut.b "
                         "Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: vmhost Personality: esx_server "
                         "Service: vmseasoning Instance: salt "
                         "Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: vmhost Personality: esx_server "
                         "Service: vmseasoning Instance: pepper "
                         "Map: Building ut",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapService)
    unittest.TextTestRunner(verbosity=2).run(suite)
