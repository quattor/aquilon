# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016,2017,2018  Contributor
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

from operator import attrgetter
import logging

from sqlalchemy.inspection import inspect

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.templates import (Plenary, ObjectPlenary, StructurePlenary,
                                      PlenaryCollection, PlenaryPersonalityBase,
                                      PlenaryResource,
                                      PlenaryServiceInstanceClientDefault,
                                      PlenaryServiceInstanceData,
                                      add_location_info)
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_include,
                                               pan_append)
from aquilon.worker.dbwrappers.cluster import get_cluster_location_preference
from aquilon.worker.locks import CompileKey, PlenaryKey


LOGGER = logging.getLogger(__name__)


class PlenaryMetaCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryMetaCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER, allow_incomplete=True):
        super(PlenaryMetaCluster, self).__init__(logger=logger,
                                                 allow_incomplete=allow_incomplete)

        self.append(PlenaryMetaClusterObject.get_plenary(dbcluster,
                                                         allow_incomplete=allow_incomplete))
        self.append(PlenaryMetaClusterData.get_plenary(dbcluster,
                                                       allow_incomplete=allow_incomplete))


class PlenaryMetaClusterData(StructurePlenary):
    prefix = "clusterdata"

    @classmethod
    def template_name(cls, dbmetacluster):
        return cls.prefix + "/" + dbmetacluster.name

    def body(self, lines):
        pan_assign(lines, "system/metacluster/name", self.dbobj.name)
        pan_assign(lines, "system/metacluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        add_location_info(lines, dbloc, prefix="system/metacluster/")
        pan_assign(lines, "system/metacluster/sysloc/location", dbloc.sysloc())

        preferred_location = get_cluster_location_preference(self.dbobj)
        if preferred_location:
            path = "system/metacluster/preferred_location"
            path = path + "/" + preferred_location.location_type
            pan_assign(lines, path, preferred_location.name)

        lines.append("")

        pan_assign(lines, "system/metacluster/members",
                   sorted(member.name for member in self.dbobj.members))

        lines.append("")

        pan_assign(lines, "system/build", self.dbobj.status.name)

        if self.dbobj.virtual_switch:
            pan_assign(lines, "system/metacluster/virtual_switch",
                       self.dbobj.virtual_switch.name)

        lines.append("")
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(lines, "system/resources/" + resource.resource_type,
                           StructureTemplate(res_path))


class PlenaryMetaClusterObject(ObjectPlenary):
    prefix = "clusters"

    @classmethod
    def template_name(cls, dbmetacluster):
        return cls.prefix + "/" + dbmetacluster.name

    def get_key(self, exclusive=True):
        keylist = [super(PlenaryMetaClusterObject, self).get_key(exclusive=exclusive)]

        if not inspect(self.dbobj).deleted:
            keylist.append(PlenaryKey(exclusive=False,
                                      personality=self.dbobj.personality_stage,
                                      logger=self.logger))
            keylist.extend(PlenaryKey(exclusive=False, service_instance=si,
                                      logger=self.logger)
                           for si in self.dbobj.services_used)
            if self.dbobj.virtual_switch:
                keylist.append(PlenaryKey(exclusive=False,
                                          virtual_switch=self.dbobj.virtual_switch,
                                          logger=self.logger))
        return CompileKey.merge(keylist)

    def body(self, lines):
        # Collect configuration of used services
        services = []
        services_data = {}
        for si in self.dbobj.services_used:
            services.append(PlenaryServiceInstanceClientDefault.template_name(si))
            services_data[si.service.name] = PlenaryServiceInstanceData.template_name(si)
        services.sort()

        # Allow settings such as loadpath to be modified by the archetype before anything else happens
        # Included only if object_declarations_template option is true
        # It the option is true, the template MUST exist
        if self.config.getboolean("panc", "object_declarations_template"):
            pan_include(lines, "archetype/declarations")
            lines.append("")

        pan_include(lines, ["pan/units", "pan/functions"])
        lines.append("")

        # Okay, here's the real content
        pan_assign(lines, "/",
                   StructureTemplate("clusterdata/%s" % self.dbobj.name,
                                     {"metadata": PanValue("/metadata")}))

        # Include service data
        for service_name in sorted(services_data.keys()):
            pan_assign(lines, "/system/services/%s" % service_name,
                       StructureTemplate(services_data[service_name]))

        pan_include(lines, "archetype/base")

        for servinst in sorted(self.dbobj.services_used):
            path = PlenaryServiceInstanceClientDefault.template_name(servinst)
            pan_include(lines, path)

        path = PlenaryPersonalityBase.template_name(self.dbobj.personality_stage)
        pan_include(lines, path)
        pan_include(lines, "archetype/final")


Plenary.handlers[MetaCluster] = PlenaryMetaCluster
