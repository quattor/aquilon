#!/usr/bin/env python
# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Module for testing the add archetype command."""

import unittest

if __name__ == "__main__":
    import utils
    utils.import_depends()

from brokertest import TestBrokerCommand

archetypes = {
    'aquilon': {
        'compilable': True,
    },
    'aurora': {
        'compilable': True,
    },
    'esx_cluster': {
        'cluster_type': 'esx',
        'compilable': True,
        'description': 'ESX',
    },
    'f5': {},
    'filer': {
        'compilable': True,
    },
    'gridcluster': {
        'cluster_type': 'compute',
        'compilable': True,
        'description': 'Grid',
    },
    'hacluster': {
        'cluster_type': 'compute',
        'compilable': True,
        'description': 'High Availability',
    },
    'metacluster': {
        'cluster_type': 'meta',
        'compilable': True,
        'description': 'ESX',
    },
    'netinfra': {
        'compilable': True,
    },
    'storagecluster': {
        'cluster_type': 'storage',
        'description': 'Storage',
    },
    'utappliance': {},
    'utarchetype1': {},
    'utarchetype2': {
        'comments': 'Some arch comments',
    },
    'utarchetype3': {},
    'vmhost': {
        'compilable': True,
    },
    'windows': {},
}


class TestAddArchetype(TestBrokerCommand):

    def test_100_add_archetypes(self):
        for arch, params in archetypes.items():
            command = ["add_archetype", "--archetype", arch]
            if params.get("compilable", False):
                command.append("--compilable")
            for opt in ("cluster_type", "description", "comments"):
                if opt in params:
                    command.extend(["--" + opt, params[opt]])

            self.noouttest(command)

    def test_105_show_archetypes(self):
        for arch, params in archetypes.items():
            command = ["show_archetype", "--archetype", arch]
            out = self.commandtest(command)

            if "cluster_type" in params:
                self.matchoutput(out, "Cluster Archetype: " + arch, command)
            else:
                self.matchoutput(out, "Host Archetype: " + arch, command)

            if params.get("compilable", False):
                self.matchoutput(out, "compilable", command)
            else:
                self.matchclean(out, "compilable", command)

            if "comments" in params:
                self.matchoutput(out, "Comments: " + params["comments"],
                                 command)
            self.matchclean(out, "Required Service", command)

    def test_105_show_archetypes_proto(self):
        for arch, params in archetypes.items():
            command = ["show_archetype", "--archetype", arch, "--format", "proto"]
            res = self.protobuftest(command, expect=1)[0]
            self.assertEqual(res.name, arch)
            self.assertEqual(res.compileable, params.get("compilable", False))
            if "cluster_type" in params:
                self.assertEqual(res.cluster_type, params["cluster_type"])
            else:
                self.assertEqual(res.cluster_type, "")

    def test_200_add_reserved_name(self):
        command = "add archetype --archetype hardware"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype name hardware is reserved.", command)

    def test_200_add_existing(self):
        command = "add archetype --archetype aquilon"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "Archetype aquilon already exists.", command)

    def test_200_add_bad_name(self):
        command = "add archetype --archetype oops@!"
        out = self.badrequesttest(command.split(" "))
        self.matchoutput(out, "'oops@!' is not a valid value for --archetype.",
                         command)

    def test_200_add_bad_cluster(self):
        command = ["add_archetype", "--archetype", "bad-cluster",
                   "--cluster_type", "bad-cluster-type"]
        out = self.badrequesttest(command)
        self.matchoutput(out,
                         "Unknown cluster type 'bad-cluster-type'. The valid "
                         "values are: compute, esx, meta, storage.",
                         command)

    def test_200_show_nonexistant(self):
        command = "show archetype --archetype archetype-does-not-exist"
        self.notfoundtest(command.split(" "))

    def test_300_verify_all(self):
        command = "show archetype --all"
        out = self.commandtest(command.split(" "))
        self.matchoutput(out, "Archetype: utarchetype1", command)
        self.matchoutput(out, "Archetype: utarchetype2", command)
        self.matchoutput(out, "Archetype: aquilon [compilable]", command)
        self.matchoutput(out, "Cluster Archetype: hacluster", command)

if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(TestAddArchetype)
    unittest.TextTestRunner(verbosity=2).run(suite)
