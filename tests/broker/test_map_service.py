#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Module for testing the map service command."""

if __name__ == "__main__":
    import utils
    utils.import_depends()

import unittest2 as unittest
from brokertest import TestBrokerCommand

default_maps = {
    "afs": {
        "q.ny.ms.com": {
            "building": ["ut", "np"],
            "city": ["ex"],
        },
    },
    "aqd": {
        "ny-prod": {
            "campus": ["ny"],
            "city": ["ex"],
        },
    },
    "bootserver": {
        "unittest": {
            "building": ["ut", "cards"],
        },
        "one-nyp": {
            "building": ["np"],
        },
    },
    "dns": {
        "unittest": {
            "building": ["ut", "cards"],
        },
        "one-nyp": {
            "building": ["np"],
        },
    },
    "lemon": {
        "ny-prod": {
            "campus": ["ny"],
            "city": ["ex"],
        },
    },
    "ntp": {
        "pa.ny.na": {
            "city": ["ny", "ex"],
        },
    },
    "syslogng": {
        "ny-prod": {
            "campus": ["ny"],
            "city": ["ex"],
        },
    },
    "support-group": {
        "ec-service": {
            "organization": ["ms"],
        },
    },
}


class TestMapService(TestBrokerCommand):
    def testmapdefaults(self):
        for service, maps in default_maps.items():
            for instance, locations in maps.items():
                for loc_type, loc_names in locations.items():
                    for loc_name in loc_names:
                        self.noouttest(["map_service", "--service", service,
                                        "--instance", instance,
                                        "--" + loc_type, loc_name])

    def testverifydefaults(self):
        command = ["show_map", "--all"]
        mapstr = "Archetype: aquilon Service: %s Instance: %s Map: %s %s"
        out = self.commandtest(command)
        for service, maps in default_maps.items():
            for instance, locations in maps.items():
                for loc_type, loc_names in locations.items():
                    for loc_name in loc_names:
                        self.matchoutput(out, mapstr % (service, instance,
                                                        loc_type.capitalize(),
                                                        loc_name),
                                         command)

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

    def testverifymapdnsut(self):
        command = ["show", "map", "--building", "ut", "--service", "dns"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: unittest Map: Building ut",
                         command)
        self.matchclean(out, "cards", command)
        self.matchclean(out, "one-nyp", command)

    def testverifymapdnsinstance(self):
        command = ["show", "map", "--service", "dns", "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: unittest Map: Building cards",
                         command)
        self.matchclean(out, "one-nyp", command)

    def testverifymapbootserver(self):
        command = ["show_map", "--service", "bootserver",
                   "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: bootserver "
                         "Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: bootserver "
                         "Instance: unittest Map: Building cards",
                         command)
        self.matchclean(out, "Building np", command)

    def testmaputsi1(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi1"])
        self.noouttest(["map", "service", "--building", "cards",
                        "--service", "utsvc", "--instance", "utsi1"])
        self.noouttest(["map", "service", "--building", "np",
                        "--service", "utsvc", "--instance", "utsi1"])

    def testmaputsi2(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi2"])
        # Do NOT bind utsi2 to "np" to keep test_compile results consistent
        #self.noouttest(["map", "service", "--building", "np",
        #                "--service", "utsvc", "--instance", "utsi2"])

    def testverifymaputsvc(self):
        command = "show map --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi1 Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi1 Map: Building cards",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi2 Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: utsvc "
                         "Instance: utsi1 Map: Building np",
                         command)
        # See testmaputsi2
        #self.matchoutput(out,
        #                 "Archetype: aquilon Service: utsvc "
        #                 "Instance: utsi2 Map: Building np",
        #                 command)

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
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def testmaputsilpersona2(self):
        self.noouttest(["add_personality", "--personality", "testme",
                        "--eon_id", "2", "--archetype", "aquilon",
                        "--copy_from", "lemon-collector-oracle",
                        "--host_environment", "dev"])

        command = ["show_map", "--archetype=aquilon",
                   "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: testme "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def testverifymapwihtoutarchetype(self):
        command = ["show_map",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def testverifymapwihtoutpersonality(self):
        command = ["show_map", "--archetype=aquilon", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: testme "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
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

    def testzcleanup(self):
        self.successtest(["del_personality", "--personality", "testme",
                          "--archetype", "aquilon"])

    def testverifyparents(self):
        command = ["show_map", "--rack", "ut3", "--include_parents"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: afs "
                         "Instance: q.ny.ms.com Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: bootserver "
                         "Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: ntp "
                         "Instance: pa.ny.na Map: City ny",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: aqd "
                         "Instance: ny-prod Map: Campus ny",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Service: dns "
                         "Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)
        self.matchclean(out, "Building np", command)
        self.matchclean(out, "Building cards", command)


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapService)
    unittest.TextTestRunner(verbosity=2).run(suite)
