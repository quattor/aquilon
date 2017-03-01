# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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
""" Formatter for building and cluster preference tables. """

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import BuildingPreference, Building


class BuildingClusterPreference(object):
    __slots__ = ['buildings', 'prefer', 'clusters', 'archetype']

    def __init__(self, buildings, archetype, clusters, prefer=None):
        self.buildings = buildings
        self.archetype = archetype
        self.clusters = clusters
        self.prefer = prefer


class BuildingPreferenceFormatter(ObjectFormatter):

    def format_raw(self, db_pref, indent="", embedded=True,
                   indirect_attrs=True):
        details = []
        details.append(indent + "Building Pair: {0.sorted_name}  {1:c}: "
                       "{1.name}  Prefer: {2.name}".format(db_pref,
                       db_pref.archetype, db_pref.prefer))
        return "\n".join(details)

    def fill_proto(self, db_pref, skeleton, embedded=True, indirect_attrs=True):
        self.redirect_proto(db_pref.a, skeleton.location.add(),
                            indirect_attrs=False)
        self.redirect_proto(db_pref.b, skeleton.location.add(),
                            indirect_attrs=False)
        self.redirect_proto(db_pref.prefer, skeleton.prefer,
                            indirect_attrs=False)
        # FIXME
        #skeleton.archetype.name = db_pref.archetype.name

ObjectFormatter.handlers[BuildingPreference] = BuildingPreferenceFormatter()

class BuildingClusterPreferenceFormatter(ObjectFormatter):

    def format_raw(self, bcpref, indent="", embedded=True, indirect_attrs=True):
        details = []
        if bcpref.prefer:
            details.append(indent + "Building Pair: {0}  {1:c}: {1.name}  "
                           "Prefer: {2.name}".format(bcpref.buildings,
                                                     bcpref.archetype,
                                                     bcpref.prefer))
        else:
            details.append(indent + "Building Pair: {0}  {1:c}: {1.name}"
                           .format(bcpref.buildings, bcpref.archetype))
        for dbcluster in bcpref.clusters:
            if dbcluster.preferred_location:
                details.append(indent + "  Cluster: {0.name}  Prefer: {1.name}"
                               .format(dbcluster, dbcluster.preferred_location))
            else:
                details.append(indent + "  Cluster: {0.name}".format(dbcluster))

        return "\n".join(details)

ObjectFormatter.handlers[BuildingClusterPreference] = BuildingClusterPreferenceFormatter()

