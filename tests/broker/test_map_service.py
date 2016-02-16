#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

import unittest
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
    "capacity_test": {
        "max_clients": {
            "building": ["ut"],
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
    "ips": {
        "northamerica": {
            "building": ["ut"],
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
    def test_100_map_defaults(self):
        for service, maps in default_maps.items():
            for instance, locations in maps.items():
                for loc_type, loc_names in locations.items():
                    for loc_name in loc_names:
                        self.noouttest(["map_service", "--service", service,
                                        "--instance", instance,
                                        "--" + loc_type, loc_name])

    def test_105_verify_defaults(self):
        command = ["show_map", "--all"]
        mapstr = "Service: %s Instance: %s Map: %s %s"
        out = self.commandtest(command)
        for service, maps in default_maps.items():
            for instance, locations in maps.items():
                for loc_type, loc_names in locations.items():
                    for loc_name in loc_names:
                        self.matchoutput(out, mapstr % (service, instance,
                                                        loc_type.capitalize(),
                                                        loc_name),
                                         command)

    def test_105_verify_afs(self):
        command = "show map --service afs --instance q.ny.ms.com --building ut"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Service: afs Instance: q.ny.ms.com Map: Building ut",
                         command)

    def test_105_verify_dns_ut(self):
        command = ["show", "map", "--building", "ut", "--service", "dns"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: dns Instance: unittest Map: Building ut",
                         command)
        self.matchclean(out, "cards", command)
        self.matchclean(out, "one-nyp", command)

    def test_105_verify_dns_instance(self):
        command = ["show", "map", "--service", "dns", "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: dns Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: dns Instance: unittest Map: Building cards",
                         command)
        self.matchclean(out, "one-nyp", command)

    def test_105_verify_bootserver(self):
        command = ["show_map", "--service", "bootserver",
                   "--instance", "unittest"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: bootserver Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: bootserver Instance: unittest Map: Building cards",
                         command)
        self.matchclean(out, "Building np", command)

    def test_110_map_utsi1(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi1"])
        self.noouttest(["map", "service", "--building", "cards",
                        "--service", "utsvc", "--instance", "utsi1"])
        self.noouttest(["map", "service", "--building", "np",
                        "--service", "utsvc", "--instance", "utsi1"])

    def test_111_map_utsi2(self):
        self.noouttest(["map", "service", "--building", "ut",
                        "--service", "utsvc", "--instance", "utsi2"])
        # Do NOT bind utsi2 to "np" to keep test_compile results consistent
        # self.noouttest(["map", "service", "--building", "np",
        #                "--service", "utsvc", "--instance", "utsi2"])

    def test_115_verify_utsvc(self):
        command = "show map --service utsvc"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out,
                         "Service: utsvc Instance: utsi1 Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: utsvc Instance: utsi1 Map: Building cards",
                         command)
        self.matchoutput(out,
                         "Service: utsvc Instance: utsi2 Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: utsvc Instance: utsi1 Map: Building np",
                         command)
        # See testmaputsi2
        # self.matchoutput(out,
        #                 "Service: utsvc Instance: utsi2 Map: Building np",
        #                 command)

    def test_120_map_chooser(self):
        for service in ["chooser1", "chooser2", "chooser3"]:
            for n in ['a', 'b', 'c']:
                if service == 'chooser2' and n == 'b':
                    continue
                if service == 'chooser3' and n == 'c':
                    continue
                instance = "ut.%s" % n
                self.noouttest(["map", "service", "--building", "ut",
                                "--service", service, "--instance", instance])

    def test_130_personality_map(self):
        self.noouttest(["map", "service", "--organization", "ms",
                        "--service", "utsvc", "--instance", "utsi2",
                        "--archetype", "aquilon",
                        "--personality", "lemon-collector-oracle"])

    def test_135_verify_personality_map(self):
        command = ["show_map", "--archetype=aquilon",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def test_135_verify_personality_no_archetype(self):
        command = ["show_map",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def test_135_verify_personality_map_proto(self):
        command = ["show_map", "--format=proto", "--archetype=aquilon",
                   "--personality=lemon-collector-oracle", "--service=utsvc"]
        map = self.protobuftest(command, expect=1)[0]
        self.assertEqual(map.location.name, 'ms')
        self.assertEqual(map.location.location_type, 'company')
        self.assertEqual(map.service.name, 'utsvc')
        self.assertEqual(map.service.serviceinstances[0].name, 'utsi2')
        self.assertEqual(map.personality.name, 'lemon-collector-oracle')
        self.assertEqual(map.personality.archetype.name, 'aquilon')

    def test_140_add_test_map(self):
        self.noouttest(["add_personality", "--personality", "svc_map_test",
                        "--eon_id", "2", "--archetype", "aquilon",
                        "--copy_from", "lemon-collector-oracle",
                        "--host_environment", "dev"])

        command = ["show_map", "--archetype=aquilon",
                   "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: svc_map_test "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def test_200_verify_nomatch(self):
        command = "show map --service afs --instance q.ny.ms.com --organization ms"
        out = self.notfoundtest(command.split(" "))
        self.matchoutput(out, "No matching map found.", command)

    def test_200_map_windows(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--archetype", "windows"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)

    def test_200_map_generic(self):
        command = ["map", "service", "--organization", "ms",
                   "--service", "utsvc", "--instance", "utsi2",
                   "--personality", "generic"]
        out = self.badoptiontest(command)
        self.matchoutput(out, "Not all mandatory options specified!", command)

    def test_200_scope_conflict(self):
        ip = self.net["netsvcmap"].subnet()[0].ip

        command = ["map", "service", "--networkip", ip,
                   "--service", "afs", "--instance", "afs-by-net",
                   "--building", "whatever"]
        out = self.badoptiontest(command)

        self.matchoutput(out,
                         "Please provide exactly one of the required options!",
                         command)

    def test_300_show_map_building_proto(self):
        command = "show map --building ut --format proto"
        self.protobuftest(command.split(" "))

    def test_300_verify_parents(self):
        command = ["show_map", "--rack", "ut3", "--include_parents"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Service: afs Instance: q.ny.ms.com Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: bootserver Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Service: ntp Instance: pa.ny.na Map: City ny",
                         command)
        self.matchoutput(out,
                         "Service: aqd Instance: ny-prod Map: Campus ny",
                         command)
        self.matchoutput(out,
                         "Service: dns Instance: unittest Map: Building ut",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)
        self.matchclean(out, "Building np", command)
        self.matchclean(out, "Building cards", command)

    def test_300_show_map_archetype(self):
        command = ["show_map", "--archetype=aquilon", "--service=utsvc"]
        out = self.commandtest(command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: lemon-collector-oracle "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)
        self.matchoutput(out,
                         "Archetype: aquilon Personality: svc_map_test "
                         "Service: utsvc Instance: utsi2 Map: Organization ms",
                         command)

    def test_800_cleanup(self):
        self.successtest(["del_personality", "--personality", "svc_map_test",
                          "--archetype", "aquilon"])

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestMapService)
    unittest.TextTestRunner(verbosity=2).run(suite)
