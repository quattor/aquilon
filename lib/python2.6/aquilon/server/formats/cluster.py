# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Cluster, EsxCluster


class ClusterFormatter(ObjectFormatter):
    def format_raw(self, cluster, indent=""):
        details = [indent + "%s cluster: %s" %
                   (cluster.cluster_type, cluster.name)]
        if cluster.metacluster:
            details.append(indent + "  Metacluster: %s" %
                           cluster.metacluster.name)
        details.append(self.redirect_raw(cluster.location_constraint,
                                         indent + "  "))
        details.append(indent + "  Max members: %s" % cluster.max_hosts)
        if hasattr(cluster, "vm_to_host_ratio"):
            details.append(indent + "  Max vm_to_host_ratio: %s" %
                           cluster.vm_to_host_ratio)
            details.append(indent + "  Current vm_to_host_ratio: %s:%s" %
                           (len(cluster.machines), len(cluster.hosts)))
            details.append(indent + "  Virtual Machine count: %s" %
                           len(cluster.machines))
        details.append(self.redirect_raw(cluster.personality, indent + "  "))
        details.append(self.redirect_raw(cluster.domain, indent + "  "))
        for dbsi in cluster.service_bindings:
            details.append(indent +
                           "  Member Alignment: Service %s Instance %s" %
                           (dbsi.service.name, dbsi.name))
        for host in cluster.hosts:
            details.append(indent + "  Member: %s" % host.fqdn)
        if cluster.comments:
            details.append(indent + "  Comments: %s" % cluster.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Cluster] = ClusterFormatter()
ObjectFormatter.handlers[EsxCluster] = ClusterFormatter()


class SimpleClusterList(list):
    """By convention, holds a list of clusters to be formatted in a simple
       (name-only) manner."""
    pass


class SimpleClusterListFormatter(ListFormatter):
    def format_raw(self, sclist, indent=""):
        return str("\n".join([indent + cluster.name for cluster in sclist]))

ObjectFormatter.handlers[SimpleClusterList] = SimpleClusterListFormatter()
