# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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


import logging

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_include,
                                               pan_append)
from aquilon.worker.locks import CompileKey


LOGGER = logging.getLogger(__name__)


class PlenaryMetaCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryMetaCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=logger)
        self.dbobj = dbcluster
        self.plenaries.append(PlenaryMetaClusterObject(dbcluster, logger=logger))
        self.plenaries.append(PlenaryMetaClusterData(dbcluster, logger=logger))


class PlenaryMetaClusterData(Plenary):

    template_type = "structure"

    def __init__(self, dbmetacluster, logger=LOGGER):
        Plenary.__init__(self, dbmetacluster, logger=logger)
        self.name = dbmetacluster.name

        # TODO maybe metaclusterdata
        self.plenary_core = "clusterdata"
        self.plenary_template = dbmetacluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        pan_assign(lines, "system/metacluster/name", self.name)
        pan_assign(lines, "system/metacluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        pan_assign(lines, "system/metacluster/sysloc/location", dbloc.sysloc())
        if dbloc.continent:
            pan_assign(lines, "system/metacluster/sysloc/continent",
                       dbloc.continent.name)
        if dbloc.city:
            pan_assign(lines, "system/metacluster/sysloc/city", dbloc.city.name)
        if dbloc.campus:
            pan_assign(lines, "system/metacluster/sysloc/campus",
                       dbloc.campus.name)
            ## maintaining this so templates dont break
            ## during transtion period.. should be DEPRECATED
            pan_assign(lines, "system/metacluster/campus", dbloc.campus.name)
        if dbloc.building:
            pan_assign(lines, "system/metacluster/sysloc/building",
                       dbloc.building.name)
        if dbloc.rack:
            pan_assign(lines, "system/metacluster/rack/row",
                       dbloc.rack.rack_row)
            pan_assign(lines, "system/metacluster/rack/column",
                       dbloc.rack.rack_column)
            pan_assign(lines, "system/metacluster/rack/name",
                       dbloc.rack.name)

        lines.append("")

        pan_assign(lines, "system/metacluster/members",
                   [member.name for member in self.dbobj.members])

        lines.append("")

        pan_assign(lines, "system/build", self.dbobj.status.name)

        lines.append("")
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources):
                pan_append(lines, "system/resources/" + resource.resource_type,
                           StructureTemplate(resource.template_base +
                                             '/config'))


class PlenaryMetaClusterObject(Plenary):

    template_type = "object"

    def __init__(self, dbmetacluster, logger=LOGGER):
        Plenary.__init__(self, dbmetacluster, logger=logger)
        self.name = dbmetacluster.name

        self.loadpath = self.dbobj.personality.archetype.name
        self.plenary_core = "clusters"
        self.plenary_template = dbmetacluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        pan_assign(lines, "/",
                   StructureTemplate("clusterdata/%s" % self.name,
                                     {"metadata": PanValue("/metadata")}))
        pan_include(lines, "archetype/base")

        #for esx_management_server
        for servinst in sorted(self.dbobj.service_bindings):
            pan_include(lines, "service/%s/%s/client/config" %
                        (servinst.service.name, servinst.name))

        pan_include(lines, "personality/%s/config" %
                    self.dbobj.personality.name)
        pan_include(lines, "archetype/final")


Plenary.handlers[MetaCluster] = PlenaryMetaCluster
