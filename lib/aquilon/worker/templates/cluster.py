# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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
from operator import attrgetter

from aquilon.aqdb.model import (Cluster, EsxCluster, ComputeCluster,
                                StorageCluster)
from aquilon.worker.templates import (Plenary, ObjectPlenary, StructurePlenary,
                                      PlenaryCollection, PlenaryResource,
                                      PlenaryServiceInstanceClientDefault,
                                      PlenaryPersonalityBase)
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_include,
                                               pan_append)
from aquilon.worker.locks import CompileKey


LOGGER = logging.getLogger(__name__)


class PlenaryCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER):
        super(PlenaryCluster, self).__init__(logger=logger)

        self.dbobj = dbcluster
        self.plenaries.append(PlenaryClusterObject(dbcluster, logger=logger))
        self.plenaries.append(PlenaryClusterData(dbcluster, logger=logger))
        self.plenaries.append(PlenaryClusterClient(dbcluster, logger=logger))


Plenary.handlers[Cluster] = PlenaryCluster
Plenary.handlers[ComputeCluster] = PlenaryCluster
Plenary.handlers[EsxCluster] = PlenaryCluster
Plenary.handlers[StorageCluster] = PlenaryCluster


class PlenaryClusterData(StructurePlenary):

    @classmethod
    def template_name(cls, dbcluster):
        return "clusterdata/" + dbcluster.name

    def __init__(self, dbcluster, logger=LOGGER):
        super(PlenaryClusterData, self).__init__(dbcluster, logger=logger)

        self.name = dbcluster.name
        if dbcluster.metacluster:
            self.metacluster = dbcluster.metacluster.name
        else:
            self.metacluster = None
        self.plenary_core = "clusterdata"
        self.plenary_template = dbcluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.template_name(self.dbobj),
                          logger=self.logger)

    def body(self, lines):
        pan_assign(lines, "system/cluster/name", self.name)
        pan_assign(lines, "system/cluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        pan_assign(lines, "system/cluster/sysloc/location", dbloc.sysloc())
        if dbloc.continent:
            pan_assign(lines, "system/cluster/sysloc/continent",
                       dbloc.continent.name)
        if dbloc.city:
            pan_assign(lines, "system/cluster/sysloc/city", dbloc.city.name)
        if dbloc.campus:
            pan_assign(lines, "system/cluster/sysloc/campus",
                       dbloc.campus.name)
            ## maintaining this so templates dont break
            ## during transtion period.. should be DEPRECATED
            pan_assign(lines, "system/cluster/campus", dbloc.campus.name)
        if dbloc.building:
            pan_assign(lines, "system/cluster/sysloc/building",
                       dbloc.building.name)
        if dbloc.bunker:
            pan_assign(lines, "system/cluster/sysloc/bunker", dbloc.bunker.name)
        if dbloc.rack:
            pan_assign(lines, "system/cluster/rack/row", dbloc.rack.rack_row)
            pan_assign(lines, "system/cluster/rack/column",
                       dbloc.rack.rack_column)
            pan_assign(lines, "system/cluster/rack/name", dbloc.rack.name)
        if dbloc.room:
            pan_assign(lines, "system/cluster/rack/room", dbloc.room)

        pan_assign(lines, "system/cluster/down_hosts_threshold",
                   self.dbobj.dht_value)
        if self.dbobj.dmt_value is not None:
            pan_assign(lines, "system/cluster/down_maint_threshold",
                       self.dbobj.dmt_value)
        if self.dbobj.down_hosts_percent:
            pan_assign(lines, "system/cluster/down_hosts_percent",
                         self.dbobj.down_hosts_threshold)
            pan_assign(lines, "system/cluster/down_hosts_as_percent",
                       self.dbobj.down_hosts_percent)
        if self.dbobj.down_maint_percent:
            pan_assign(lines, "system/cluster/down_maint_percent",
                       self.dbobj.down_maint_threshold)
            pan_assign(lines, "system/cluster/down_maint_as_percent",
                       self.dbobj.down_maint_percent)
        lines.append("")
        # Only use system names here to avoid circular dependencies.
        # Other templates that needs to look up the underlying values use:
        # foreach(idx; host; value("system/cluster/members")) {
        #     v = value("/" + host + "/system/foo/bar/baz");
        # );
        pan_assign(lines, "system/cluster/members",
                   sorted([member.fqdn for member in self.dbobj.hosts]))

        lines.append("")
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(lines, "system/resources/" + resource.resource_type,
                           StructureTemplate(res_path))
        pan_assign(lines, "system/build", self.dbobj.status.name)
        if self.dbobj.allowed_personalities:
            pan_assign(lines, "system/cluster/allowed_personalities",
                       sorted(["%s/%s" % (p.archetype.name, p.name)
                               for p in self.dbobj.allowed_personalities]))

        fname = "body_%s" % self.dbobj.cluster_type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_esx(self, lines):
        if self.metacluster:
            pan_assign(lines, "system/metacluster/name", self.metacluster)
        pan_assign(lines, "system/cluster/ratio", [self.dbobj.vm_count,
                                                    self.dbobj.host_count])
        pan_assign(lines, "system/cluster/max_hosts",
                   self.dbobj.max_hosts)
        lines.append("")

        lines.append("")
        if isinstance(self.dbobj, EsxCluster) and self.dbobj.switch:
            pan_assign(lines, "system/cluster/switch",
                       self.dbobj.switch.primary_name)


class PlenaryClusterObject(ObjectPlenary):
    """
    A cluster has its own output profile, so the plenary cluster template
    is an object template that includes the data about which machines
    are contained inside the cluster (via an include of the clusterdata plenary)
    """

    @classmethod
    def template_name(cls, dbcluster):
        return "clusters/" + dbcluster.name

    def __init__(self, dbcluster, logger=LOGGER):
        super(PlenaryClusterObject, self).__init__(dbcluster, logger=logger)

        self.name = dbcluster.name
        self.loadpath = dbcluster.personality.archetype.name
        self.plenary_core = "clusters"
        self.plenary_template = dbcluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.template_name(self.dbobj),
                          logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        path = PlenaryClusterData.template_name(self.dbobj)
        pan_assign(lines, "/",
                   StructureTemplate(path,
                                     {"metadata": PanValue("/metadata")}))
        pan_include(lines, "archetype/base")

        for servinst in sorted(self.dbobj.service_bindings):
            path = PlenaryServiceInstanceClientDefault.template_name(servinst)
            pan_include(lines, path)

        path = PlenaryPersonalityBase.template_name(self.dbobj.personality)
        pan_include(lines, path)
        pan_include(lines, "archetype/final")


class PlenaryClusterClient(Plenary):
    """
    A host that is a member of a cluster will include the cluster client
    plenary template. This just names the cluster and nothing more.
    """

    @classmethod
    def template_name(cls, dbcluster):
        return "cluster/%s/client" % dbcluster.name

    def __init__(self, dbcluster, logger=LOGGER):
        super(PlenaryClusterClient, self).__init__(dbcluster, logger=logger)

        self.name = dbcluster.name
        self.plenary_core = "cluster/%s" % self.name
        self.plenary_template = "client"

    def get_key(self):
        # This takes a domain lock because it could affect all clients...
        return CompileKey(domain=self.dbobj.branch.name, logger=self.logger)

    def body(self, lines):
        pan_assign(lines, "/system/cluster/name", self.name)
        # We could just use a PAN external reference to pull in this value from
        # the cluster template, but since we know that these templates are
        # always in sync, we can duplicate the content here to avoid the
        # possibility of circular external references.
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources,
                                   key=attrgetter('resource_type', 'name')):
                res_path = PlenaryResource.template_name(resource)
                pan_append(lines, "/system/cluster/resources/" +
                           resource.resource_type, StructureTemplate(res_path))
        lines.append("include { if_exists('features/' + value('/system/archetype/name') + '/%s/%s/config') };"
                     % (self.dbobj.personality.archetype.name,
                        self.dbobj.personality.name))
