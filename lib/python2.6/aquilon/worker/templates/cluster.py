# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.


import logging

from aquilon.aqdb.model import (Cluster, EsxCluster, ComputeCluster,
                                StorageCluster)
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.panutils import (StructureTemplate, pan_assign,
                                               pan_include, pan_push)
from aquilon.worker.locks import CompileKey


LOGGER = logging.getLogger(__name__)


class PlenaryCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=LOGGER)
        self.dbobj = dbcluster
        self.plenaries.append(PlenaryClusterObject(dbcluster, logger=logger))
        self.plenaries.append(PlenaryClusterData(dbcluster, logger=logger))
        self.plenaries.append(PlenaryClusterClient(dbcluster, logger=logger))


Plenary.handlers[Cluster] = PlenaryCluster
Plenary.handlers[ComputeCluster] = PlenaryCluster
Plenary.handlers[EsxCluster] = PlenaryCluster
Plenary.handlers[StorageCluster] = PlenaryCluster


class PlenaryClusterData(Plenary):

    template_type = ""

    def __init__(self, dbcluster, logger=LOGGER):
        Plenary.__init__(self, dbcluster, logger=logger)
        self.name = dbcluster.name
        if dbcluster.metacluster:
            self.metacluster = dbcluster.metacluster.name
        else:
            self.metacluster = "global"
        self.plenary_core = "clusterdata"
        self.plenary_template = dbcluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template_name, logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        lines.append("")
        pan_assign(lines, "/system/cluster/name", self.name)
        pan_assign(lines, "/system/cluster/type", self.dbobj.cluster_type)

        dbloc = self.dbobj.location_constraint
        pan_assign(lines, "/system/cluster/sysloc/location", dbloc.sysloc())
        if dbloc.continent:
            pan_assign(lines, "/system/cluster/sysloc/continent",
                       dbloc.continent.name)
        if dbloc.city:
            pan_assign(lines, "/system/cluster/sysloc/city", dbloc.city.name)
        if dbloc.campus:
            pan_assign(lines, "/system/cluster/sysloc/campus",
                       dbloc.campus.name)
            ## maintaining this so templates dont break
            ## during transtion period.. should be DEPRECATED
            pan_assign(lines, "/system/cluster/campus", dbloc.campus.name)
        if dbloc.building:
            pan_assign(lines, "/system/cluster/sysloc/building",
                       dbloc.building.name)
        if dbloc.rack:
            pan_assign(lines, "/system/cluster/rack/row", dbloc.rack.rack_row)
            pan_assign(lines, "/system/cluster/rack/column",
                       dbloc.rack.rack_column)
            pan_assign(lines, "/system/cluster/rack/name", dbloc.rack.name)

        pan_assign(lines, "/system/cluster/down_hosts_threshold",
                   self.dbobj.dht_value)
        if self.dbobj.dmt_value is not None:
            pan_assign(lines, "/system/cluster/down_maint_threshold",
                       self.dbobj.dmt_value)
        if self.dbobj.down_hosts_percent:
            pan_assign(lines, "/system/cluster/down_hosts_percent",
                         self.dbobj.down_hosts_threshold)
            pan_assign(lines, "/system/cluster/down_hosts_as_percent",
                       self.dbobj.down_hosts_percent)
        if self.dbobj.down_maint_percent:
            pan_assign(lines, "/system/cluster/down_maint_percent",
                       self.dbobj.down_maint_threshold)
            pan_assign(lines, "/system/cluster/down_maint_as_percent",
                       self.dbobj.down_maint_percent)
        lines.append("")
        # Only use system names here to avoid circular dependencies.
        # Other templates that needs to look up the underlying values use:
        # foreach(idx; host; value("/system/cluster/members")) {
        #     v = value("//" + host + "/system/foo/bar/baz");
        # );
        pan_assign(lines, "/system/cluster/members",
                   sorted([member.fqdn for member in self.dbobj.hosts]))

        lines.append("")
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources):
                pan_push(lines, "/system/resources/%s" % resource.resource_type,
                         StructureTemplate(resource.template_base + '/config'))
        pan_assign(lines, "/system/build", self.dbobj.status.name)
        if self.dbobj.allowed_personalities:
            pan_assign(lines, "/system/cluster/allowed_personalities",
                       sorted(["%s/%s" % (p.archetype.name, p.name)
                               for p in self.dbobj.allowed_personalities]))

        fname = "body_%s" % self.dbobj.cluster_type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_esx(self, lines):
        if self.metacluster:
            pan_assign(lines, "/system/metacluster/name", self.metacluster)
        pan_assign(lines, "/system/cluster/ratio", [self.dbobj.vm_count,
                                                    self.dbobj.host_count])
        pan_assign(lines, "/system/cluster/max_hosts",
                   self.dbobj.max_hosts)
        lines.append("")
        machines = {}
        for machine in sorted(self.dbobj.machines):
            if not machine.interfaces or not machine.disks:
                # Do not bother creating entries for VMs that are incomplete.
                continue
            pmac = Plenary.get_plenary(machine, logger=self.logger)
            macdesc = {'hardware': StructureTemplate(pmac.plenary_template_name)}

            # One day we may get to the point where this will be required.
            if (machine.host):
                # we fill this in manually instead of just assigning
                # 'system' = value("hostname:/system")
                # because the target host might not actually have a profile.
                arch = machine.host.archetype
                os = machine.host.operating_system
                pn = machine.primary_name.fqdn
                macdesc["system"] = {'archetype': {'name': arch.name,
                                                   'os': os.name,
                                                   'osversion': os.version},
                                     'network': {'hostname': pn.name,
                                                 'domainname': pn.dns_domain}}

            machines[machine.label] = macdesc
        pan_assign(lines, "/system/cluster/machines", machines)


class PlenaryClusterObject(Plenary):
    """
    A cluster has its own output profile, so the plenary cluster template
    is an object template that includes the data about which machines
    are contained inside the cluster (via an include of the clusterdata plenary)
    """

    template_type = "object"

    def __init__(self, dbcluster, logger=LOGGER):
        Plenary.__init__(self, dbcluster, logger=logger)
        self.name = dbcluster.name
        if dbcluster.metacluster:
            self.metacluster = dbcluster.metacluster.name
        else:
            self.metacluster = "global"
        self.loadpath = dbcluster.personality.archetype.name
        self.plenary_core = "clusters"
        self.plenary_template = dbcluster.name

    def get_key(self):
        return CompileKey(domain=self.dbobj.branch.name,
                          profile=self.plenary_template_name, logger=self.logger)

    def body(self, lines):
        pan_include(lines, ["pan/units", "pan/functions"])
        pan_include(lines, "clusterdata/%s" % self.name)
        pan_include(lines, "archetype/base")

        for servinst in sorted(self.dbobj.service_bindings):
            pan_include(lines, "service/%s/%s/client/config" %
                        (servinst.service.name, servinst.name))

        pan_include(lines, "personality/%s/config" %
                    self.dbobj.personality.name)
        pan_include(lines, "archetype/final")


class PlenaryClusterClient(Plenary):
    """
    A host that is a member of a cluster will include the cluster client
    plenary template. This just names the cluster and nothing more.
    """

    template_type = ""

    def __init__(self, dbcluster, logger=LOGGER):
        Plenary.__init__(self, dbcluster, logger=logger)
        self.name = dbcluster.name
        self.plenary_core = "cluster/%s" % self.name
        self.plenary_template = "client"

    def get_key(self):
        # This takes a domain lock because it could affect all clients...
        return CompileKey(domain=self.dbobj.branch.name, logger=self.logger)

    def body(self, lines):
        pan_assign(lines, "/system/cluster/name", self.name)
        # we could just use a PAN external reference to pull in this
        # value from the cluster template, i.e. using
        #  value('clusters/'+value('/system/cluster/name')+':/system/resources')
        # but since we know that these templates are always in sync,
        # we can duplicate the content here to avoid the possibility of
        # circular external references.
        if self.dbobj.resholder:
            for resource in sorted(self.dbobj.resholder.resources):
                pan_push(lines, "/system/cluster/resources/%s" %
                         resource.resource_type,
                         StructureTemplate(resource.template_base + '/config'))
        lines.append("include { if_exists('features/' + value('/system/archetype/name') + '/%s/%s/config') };"
                     % (self.dbobj.personality.archetype.name,
                        self.dbobj.personality.name))
