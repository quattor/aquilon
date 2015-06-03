# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
""" Helper classes for cluster testing """

ctype_map = {
    "esx_cluster": "esx",
    "gridcluster": "compute",
    "hacluster": "compute",
}

class ClusterTestMixin(object):
    def verify_cat_clusters(self, name, archetype, persona, ctype=None,
                            metacluster=None, on_rack=False,
                            branch_name="unittest", branch_type="domain",
                            allowed_personalities=None):
        if not ctype:
            ctype = ctype_map[archetype]

        object_command = ["cat", "--cluster", name]
        object = self.commandtest(object_command)

        self.matchoutput(object, "object template clusters/%s;" % name,
                         object_command)
        self.searchoutput(object,
                          r'variable LOADPATH = list\(\s*"%s"\s*\);' % archetype,
                          object_command)
        self.matchoutput(object, '"/" = create("clusterdata/%s"' % name,
                         object_command)
        self.matchoutput(object, '"/metadata/template/branch/name" = "%s";' %
                         branch_name, object_command)
        self.matchoutput(object, '"/metadata/template/branch/type" = "%s";' %
                         branch_type, object_command)
        if branch_type == "domain":
            self.matchclean(object,
                            '"/metadata/template/branch/author"',
                            object_command)

        self.matchoutput(object, 'include { "personality/%s/config" };' % persona,
                         object_command)

        data_command = ["cat", "--cluster", name, "--data"]
        data = self.commandtest(data_command)

        self.matchoutput(data, "structure template clusterdata/%s;" % name,
                         data_command)
        self.matchoutput(data, '"system/cluster/name" = "%s";' % name,
                         data_command)
        self.matchoutput(data, '"system/cluster/type" = "%s";' % ctype,
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/continent" = "na";',
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/country" = "us";',
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/city" = "ny";',
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/campus" = "ny";',
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/building" = "ut";',
                         data_command)
        self.matchoutput(data, '"system/cluster/sysloc/location" = "ut.ny.na";',
                         data_command)

        if metacluster:
            self.matchoutput(data, '"system/cluster/metacluster/name" = "%s";' %
                             metacluster, data_command)
            self.matchoutput(data, '"system/metacluster/name" = "%s";' %
                             metacluster, data_command)

        self.matchoutput(data, '"system/build" = "build";', data_command)
        if on_rack:
            self.matchoutput(data, '"system/cluster/rack/name" = "ut13"',
                             data_command)
            self.matchoutput(data, '"system/cluster/rack/row" = "k"',
                             data_command)
            self.matchoutput(data, '"system/cluster/rack/column" = "3"',
                             data_command)
        else:
            self.matchclean(data, '"system/cluster/rack/name"', data_command)
            self.matchclean(data, '"system/cluster/rack/row"', data_command)
            self.matchclean(data, '"system/cluster/rack/column"', data_command)

        if allowed_personalities:
            regex = ",".join(r'"%s"\s*' % allowed
                             for allowed in allowed_personalities)
            self.searchoutput(data,
                              r'"system/cluster/allowed_personalities" = list\(\s*' +
                              regex + r"\);",
                              data_command)
        else:
            self.matchclean(data, '"system/cluster/allowed_personalities"', data_command)

        self.matchclean(data, "resources/virtual_machine", data_command)

        return object_command, object, data_command, data

