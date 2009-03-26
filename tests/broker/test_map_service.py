#!/ms/dist/python/PROJ/core/2.5.2-1/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
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
                        "--service", "afs", "--instance", "q.ny.ms.com",
                        "--archetype", "aquilon"])

    def testverifymapafs(self):
        command = "show map --service afs --instance q.ny.ms.com --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype: aquilon Service: afs "
                         "Instance: q.ny.ms.com Map: Building ut",
                         command)

    def testmapdns(self):
        self.noouttest(["map", "service", "--hub", "ny",
                        "--service", "dns", "--instance", "nyinfratest",
                        "--archetype", "aquilon"])

    def testverifymapdns(self):
        command = ["show", "map", "--archetype", "aquilon",
                   "--service", "dns", "--instance", "nyinfratest",
                   "--hub", "ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: nyinfratest Map: Hub ny",
                         command)

    def testmapaqd(self):
        self.noouttest(["map", "service", "--campus", "ny",
                        "--service", "aqd", "--instance", "ny-prod",
                        "--archetype", "aquilon"])

    def testverifymapaqd(self):
        command = ["show_map", "--archetype=aquilon",
                   "--service=aqd", "--instance=ny-prod", "--campus=ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: aqd "
                         "Instance: ny-prod Map: Campus ny",
                         command)

    def testmapbootserver(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "bootserver", "--instance", "np.test",
                        "--archetype", "aquilon"])

    def testverifymapbootserver(self):
        command = ["show_map", "--service", "bootserver",
                   "--instance", "np.test", "--building", "ut",
                   "--archetype", "aquilon"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: bootserver "
                         "Instance: np.test Map: Building ut",
                         command)

    def testmapntp(self):
        self.noouttest(["map", "service", "--city", "ny",
                        "--service", "ntp", "--instance", "pa.ny.na",
                        "--archetype", "aquilon"])

    def testverifymapntp(self):
        command = ["show_map", "--archetype=aquilon",
                   "--service=ntp", "--instance=pa.ny.na", "--city=ny"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: ntp "
                         "Instance: pa.ny.na Map: City ny",
                         command)

    def testmaputsi1(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi1",
                        "--archetype", "aquilon"])

    def testmaputsi2(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi2",
                        "--archetype", "aquilon"])

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
        command = "show map --archetype aquilon --building ut --format proto"
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
                                "--archetype", "aquilon",
                                "--service", service, "--instance", instance])

    def testmaputsilpersona(self):
        self.noouttest(["map", "service", "--company", "ms",
                        "--service", "utsvc", "--instance", "utsi2",
                        "--archetype", "aquilon",
                        "--personality", "lemon-oracle"])

    def testverifymappersona(self):
        command = ["show_map", "--archetype=aquilon",
                   "--personality=lemon-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-oracle "
                         "Service: utsvc Instance: utsi2 Map: Company ms",
                         command)

    def testverifymapwihtoutarchetype(self):
        command = ["show_map",
                   "--personality=lemon-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-oracle "
                         "Service: utsvc Instance: utsi2 Map: Company ms",
                         command)

    def testverifypersonalitymapproto(self):
        command = ["show_map", "--format=proto", "--archetype=aquilon",
                   "--personality=lemon-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        servicemaplist = self.parse_servicemap_msg(out, expect=1)
        map = servicemaplist.servicemaps[0]
        self.failUnlessEqual(map.location.name, 'ms')
        self.failUnlessEqual(map.location.location_type, 'company')
        self.failUnlessEqual(map.service.name, 'utsvc')
        self.failUnlessEqual(map.service.serviceinstances[0].name, 'utsi2')
        self.failUnlessEqual(map.personality.name, 'lemon-oracle')
        self.failUnlessEqual(map.personality.archetype.name, 'aquilon')

    def testmapwindowsfail(self):
        command = ["map", "service", "--company", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "windows"]
        out = self.unimplementederrortest(command)
        self.matchoutput(out,
                         "Archetype level ServiceMaps other than "
                         "aquilon are not yet available",
                         command)

    def testverifyshowmapunimplemented(self):
        command = "show map --archetype windows"
        out = self.unimplementederrortest(command.split(" "))
        self.matchoutput(out,
                         "Archetype level ServiceMaps other than "
                         "aquilon are not yet available",
                         command)


if __name__=='__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapService)
    unittest.TextTestRunner(verbosity=2).run(suite)
