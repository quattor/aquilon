# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017,2018  Contributor
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

from sqlalchemy.inspection import inspect

from aquilon.aqdb.model import (Cluster, EsxCluster, ComputeCluster,
                                StorageCluster)
from aquilon.worker.templates import (Plenary, ObjectPlenary, StructurePlenary,
                                      PlenaryCollection, PlenaryResource,
                                      PlenaryServiceInstanceClientDefault,
                                      PlenaryServiceInstanceData,
                                      PlenaryServiceInstanceServerDefault,
                                      PlenaryPersonalityBase, add_location_info)
from aquilon.worker.templates.panutils import (StructureTemplate, PanValue,
                                               pan_assign, pan_include,
                                               pan_append)
from aquilon.worker.dbwrappers.cluster import get_cluster_location_preference
from aquilon.worker.locks import CompileKey, PlenaryKey


LOGGER = logging.getLogger(__name__)


class PlenaryCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER, allow_incomplete=True):
        super(PlenaryCluster, self).__init__(logger=logger,
                                             allow_incomplete=allow_incomplete)

        self.append(PlenaryClusterObject.get_plenary(dbcluster,
                                                     allow_incomplete=allow_incomplete))
        self.append(PlenaryClusterData.get_plenary(dbcluster,
                                                   allow_incomplete=allow_incomplete))
        self.append(PlenaryClusterClient.get_plenary(dbcluster,
                                                     allow_incomplete=allow_incomplete))


Plenary.handlers[Cluster] = PlenaryCluster
Plenary.handlers[ComputeCluster] = PlenaryCluster
Plenary.handlers[EsxCluster] = PlenaryCluster
Plenary.handlers[StorageCluster] = PlenaryCluster


class PlenaryClusterData(StructurePlenary):
    prefix = "clusterdata"

    @classmethod
    def template_name(cls, dbcluster):
        return cls.prefix + "/" + dbcluster.name

    def body(self, lines):
        pan_assign(lines, "system/cluster/name", self.dbobj.name)
        pan_assign(lines, "system/cluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        add_location_info(lines, dbloc, prefix="system/cluster/")
        pan_assign(lines, "system/cluster/sysloc/location", dbloc.sysloc())

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
                   sorted(member.fqdn for member in self.dbobj.hosts))

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
                       sorted("%s/%s" % (p.archetype.name, p.name)
                              for p in self.dbobj.allowed_personalities))

        if self.dbobj.max_hosts is not None:
            pan_assign(lines, "system/cluster/max_hosts",
                       self.dbobj.max_hosts)

        if self.dbobj.metacluster:
            pan_assign(lines, "system/cluster/metacluster/name",
                       self.dbobj.metacluster.name)

        preferred_location = get_cluster_location_preference(self.dbobj)
        if preferred_location:
            path = "system/cluster/preferred_location"
            path = path + "/" + preferred_location.location_type
            pan_assign(lines, path, preferred_location.name)

        fname = "body_%s" % self.dbobj.cluster_type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

        if self.dbobj.virtual_switch:
            pan_assign(lines, "system/cluster/virtual_switch",
                       self.dbobj.virtual_switch.name)

    def body_esx(self, lines):
        # FIXME: deprecate /system/metacluster/name
        if self.dbobj.metacluster:
            pan_assign(lines, "system/metacluster/name",
                       self.dbobj.metacluster.name)
        if self.dbobj.network_device:
            pan_assign(lines, "system/cluster/switch",
                       self.dbobj.network_device.primary_name)


class PlenaryClusterObject(ObjectPlenary):
    """
    A cluster has its own output profile, so the plenary cluster template
    is an object template that includes the data about which machines
    are contained inside the cluster (via an include of the clusterdata plenary)
    """

    prefix = "clusters"

    @classmethod
    def template_name(cls, dbcluster):
        return cls.prefix + "/" + dbcluster.name

    def get_key(self, exclusive=True):
        keylist = [super(PlenaryClusterObject, self).get_key(exclusive=exclusive)]

        if not inspect(self.dbobj).deleted:
            keylist.append(PlenaryKey(exclusive=False,
                                      personality=self.dbobj.personality_stage,
                                      logger=self.logger))
            keylist.extend(PlenaryKey(exclusive=False, service_instance=si,
                                      logger=self.logger)
                           for si in self.dbobj.services_used)
            keylist.extend(PlenaryKey(exclusive=False,
                                      service_instance=srv.service_instance,
                                      logger=self.logger)
                           for srv in self.dbobj.services_provided)

            if self.dbobj.metacluster:
                keylist.append(PlenaryKey(exclusive=False,
                                          cluster_member=self.dbobj.metacluster,
                                          logger=self.logger))
            if isinstance(self.dbobj, EsxCluster) and self.dbobj.network_device:
                # TODO: this should become a CompileKey if we start generating
                # profiles for switches
                keylist.append(PlenaryKey(exclusive=False,
                                          network_device=self.dbobj.network_device,
                                          logger=self.logger))
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
        path = PlenaryClusterData.template_name(self.dbobj)
        pan_assign(lines, "/",
                   StructureTemplate(path,
                                     {"metadata": PanValue("/metadata")}))

        # Include service data
        for service_name in sorted(services_data.keys()):
            pan_assign(lines, "/system/services/%s" % service_name,
                       StructureTemplate(services_data[service_name]))

        pan_include(lines, "archetype/base")

        for servinst in sorted(self.dbobj.services_used,
                               key=attrgetter('service.name', 'name')):
            path = PlenaryServiceInstanceClientDefault.template_name(servinst)
            pan_include(lines, path)

        for srv in sorted(self.dbobj.services_provided,
                          key=attrgetter("service_instance.service.name",
                                         "service_instance.name")):
            path = PlenaryServiceInstanceServerDefault.template_name(srv.service_instance)
            pan_include(lines, path)

        path = PlenaryPersonalityBase.template_name(self.dbobj.personality_stage)
        pan_include(lines, path)
        pan_include(lines, "archetype/final")


class PlenaryClusterClient(Plenary):
    """
    A host that is a member of a cluster will include the cluster client
    plenary template. This just names the cluster and nothing more.
    """

    prefix = "cluster"
    ignore_compileable = True

    @classmethod
    def template_name(cls, dbcluster):
        return "%s/%s/client" % (cls.prefix, dbcluster.name)

    def get_key(self, exclusive=True):
        return PlenaryKey(cluster_member=self.dbobj.name, logger=self.logger,
                          exclusive=exclusive)

    def body(self, lines):
        pan_assign(lines, "/system/cluster/name", self.dbobj.name)
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
        lines.append('include if_exists("features/" + value("/system/archetype/name") + "/%s/%s/config");'
                     % (self.dbobj.archetype.name, self.dbobj.personality.name))
