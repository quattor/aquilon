# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import (Cluster, EsxCluster, ComputeCluster,
                                StorageCluster)


class ClusterFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, cluster, skeleton):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ClusterList()
            skeleton = container.resources.add()
        skeleton.name = str(cluster.name)
        skeleton.status = str(cluster.status)
        self.add_personality_data(skeleton.personality, cluster.personality)
        skeleton.domain.name = str(cluster.branch.name)
        skeleton.domain.owner = str(cluster.branch.owner.name)

        skeleton.threshold = cluster.down_hosts_threshold
        skeleton.threshold_is_percent = cluster.down_hosts_percent
        if cluster.down_maint_threshold is not None:
            skeleton.maint_threshold = cluster.down_maint_threshold
            skeleton.maint_threshold_is_percent = \
                                           cluster.down_maint_percent

        for host in sorted(cluster.hosts, key=lambda x : x.fqdn):
            self.add_host_msg(skeleton.hosts.add(), host)

        if len(cluster.resources) > 0:
            for resource in cluster.resources:
                r = skeleton.resources.add()
                self.redirect_proto(resource, r)

        for dbsi in cluster.service_bindings:
            si = skeleton.aligned_services.add()
            si.service = dbsi.service.name
            si.instance = dbsi.name

        for personality in cluster.allowed_personalities:
            p = skeleton.allowed_personalities.add()
            p.name = str(personality.name)
            p.archetype.name = str(personality.archetype.name)

        if cluster.cluster_type == 'esx':
            skeleton.vm_to_host_ratio = cluster.vm_to_host_ratio
            skeleton.max_vm_count = cluster.max_vm_count

            caps = cluster.get_total_capacity()
            if caps:
                overrides = cluster.get_capacity_overrides()
                for name, value in caps.items():
                    v = skeleton.limits.add()
                    v.name = name
                    v.value = value
                    if overrides.get(name) is not None:
                        v.override = True

            usage = cluster.get_total_usage()
            if usage:
                for name, value in usage.items():
                    u = skeleton.usage.add()
                    u.name = name
                    u.value = value

        return container


    def format_raw(self, cluster, indent=""):
        details = [indent + "{0:c}: {0.name}".format(cluster)]
        if cluster.metacluster:
            details.append(indent + \
                           "  {0:c}: {0.name}".format(cluster.metacluster))
        details.append(self.redirect_raw(cluster.location_constraint,
                                         indent + "  "))
        details.append(indent + "  Max members: %s" % cluster.max_hosts)
        if cluster.down_hosts_percent:
            dht = int((cluster.down_hosts_threshold * len(cluster.hosts))/100)
            details.append(indent + "  Down Hosts Threshold: %s (%s%%)" %
                           (dht, cluster.down_hosts_threshold))
        else:
            details.append(indent + "  Down Hosts Threshold: %s" %
                           cluster.down_hosts_threshold)

        if cluster.down_maint_threshold is not None:
            if cluster.down_maint_percent:
                dht = int((cluster.down_maint_threshold *
                           len(cluster.hosts))/100)
                details.append(indent + "  Maintenance Threshold: %s (%s%%)" %
                           (dht, cluster.down_maint_threshold))
            else:
                details.append(indent + "  Maintenance Threshold: %s" %
                               cluster.down_maint_threshold)

        for resource in cluster.resources:
            details.append(indent + "  {0:c}: {0.name}".format(resource))

        if cluster.cluster_type == 'esx':
            details.append(indent + "  Max vm_to_host_ratio: %s" %
                           cluster.vm_to_host_ratio)
            details.append(indent + "  Max virtual machine count: %s" %
                           cluster.max_vm_count)
            details.append(indent + "  Current vm_to_host_ratio: %s:%s" %
                           (len(cluster.machines), len(cluster.hosts)))
            details.append(indent + "  Virtual Machine count: %s" %
                           len(cluster.machines))
            details.append(indent + "  ESX VMHost count: %s" %
                           len(cluster.hosts))
            if cluster.switch:
                details.append(indent + "  {0:c}: {0!s}".format(cluster.switch))
            caps = cluster.get_total_capacity()
            if caps:
                overrides = cluster.get_capacity_overrides()
                values = []
                for name, value in caps.items():
                    flags = ""
                    if overrides.get(name) is not None:
                        flags = " [override]"
                    values.append("%s: %s%s" % (name, value, flags))
                capstr = ", ".join(values)
            else:
                capstr = None
            details.append(indent + "  Capacity limits: %s" % capstr)
            usage = cluster.get_total_usage()
            if usage:
                usagestr = ", ".join(["%s: %s" % (name, value) for name, value
                                      in usage.items()])
            else:
                usagestr = None
            details.append(indent + "  Resources used by VMs: %s" % usagestr)
        details.append(self.redirect_raw(cluster.status, indent + "  "))
        details.append(self.redirect_raw(cluster.personality, indent + "  "))
        if cluster.branch.branch_type == 'domain':
            details.append(indent + "  Domain: %s" % cluster.branch.name)
        else:
            details.append(indent + "  Sandbox: %s/%s" %
                           (cluster.sandbox_author.name, cluster.branch.name))
        for dbsi in cluster.service_bindings:
            details.append(indent +
                           "  Member Alignment: Service %s Instance %s" %
                           (dbsi.service.name, dbsi.name))
        for personality in cluster.allowed_personalities:
            details.append(indent + "  Allowed Personality: {0}".format(personality))
        for host in sorted(cluster.hosts, key=lambda x : x.fqdn):
            details.append(indent + "  Member: %s" % host.fqdn)
        if cluster.comments:
            details.append(indent + "  Comments: %s" % cluster.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Cluster] = ClusterFormatter()
ObjectFormatter.handlers[EsxCluster] = ClusterFormatter()
ObjectFormatter.handlers[ComputeCluster] = ClusterFormatter()
ObjectFormatter.handlers[StorageCluster] = ClusterFormatter()


class SimpleClusterList(list):
    """By convention, holds a list of clusters to be formatted in a simple
       (name-only) manner."""
    pass


class SimpleClusterListFormatter(ListFormatter):
    def format_raw(self, sclist, indent=""):
        return str("\n".join([indent + cluster.name for cluster in sclist]))


ObjectFormatter.handlers[SimpleClusterList] = SimpleClusterListFormatter()


class ClusterList(list):
    pass


class ClusterListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_proto(self, cluslist, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].ClusterList()
        for resource in cluslist:
            self.redirect_proto(resource, skeleton.clusters.add())
        return skeleton


ObjectFormatter.handlers[ClusterList] = ClusterListFormatter()
