# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from aquilon.server.templates.base import Plenary, compileLock, compileRelease
from aquilon.server.templates.machine import PlenaryMachineInfo


class PlenaryMetaCluster(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "metacluster"
        self.plenary_template = "%(plenary_core)s/%(name)s" % self.__dict__
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        lines.append("include { 'metacluster/%(name)s/data' };" %
                     self.__dict__)


class PlenaryMetaClusterClient(Plenary):
    """
    A normal template included by cluster clients of a metacluster.
    """
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "metacluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/client" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("'/system/metacluster' = "
            "create('metacluster/%(name)s/clientdata');" % self.__dict__)


class PlenaryMetaClusterData(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "metacluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/data" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        return


class PlenaryMetaClusterClientData(Plenary):
    """
    A structure template that provides the name of the metacluster
    and a list of clusters contained within the metacluster.
    """
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "metacluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/clientdata" % self.__dict__
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")
        self.clients = [cluster.name for cluster in dbmetacluster.members]

    def body(self, lines):
        lines.append("'name' = '%s';" % self.name)
        lines.append("'clusters' = list(" +
                     ", ".join([("'" + cluster + "'")
                                for cluster in self.clients]) +
                     ");")

class PlenaryCluster(Plenary):
    """
    A cluster has its own output profile, so the plenary cluster template
    is an object template that includes the data about which machines
    are contained inside the cluster (via an include of the clusterdata plenary)
    """

    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.template_type = 'object'
        self.dbcluster = dbcluster
        self.name = dbcluster.name
        self.metacluster = "global"
        if dbcluster.metacluster:
            self.metacluster = dbcluster.metacluster.name
        self.plenary_core = ""
        self.plenary_template = "%(name)s" % self.__dict__
        self.dir = self.config.get("broker", "builddir") + \
                    "/domains/%s/clusters" % dbcluster.domain.name

    def cleanup(self, name, domain, locked=False):
        Plenary.cleanup(self, name, domain, locked)
        # And the other plenary files....
        client = PlenaryClusterClient(self.dbcluster)
        client.remove(None, locked)

    def body(self, lines):
        fname = "body_%s" % self.dbcluster.cluster_type
        if hasattr(self, fname):
            getattr(self, fname)(lines)

    def body_esx(self, lines):
        lines.append("include { 'pan/units' };")
        lines.append("")
        lines.append("'/system/cluster/name' = '%s';" % self.name)
        if self.metacluster:
            lines.append("include { 'metacluster/%(metacluster)s/client' };"
                         % self.__dict__)
        lines.append("'/system/cluster/machines' = nlist(")
        for machine in self.dbcluster.machines:
            pmac = PlenaryMachineInfo(machine)
            lines.append("    '%s', create('%s')," % (machine.name,
                                                      pmac.plenary_template))
        lines.append(");")

        for servinst in self.dbcluster.service_bindings:
            lines.append("include { 'service/%s/%s/client/config' };" % \
                         (servinst.service.name, servinst.name))


class PlenaryClusterClient(Plenary):
    """
    A host that is a member of a cluster will include the cluster client
    plenary template. This just names the cluster and nothing more.
    """
    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.name = dbcluster.name
        self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/client" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("'/system/cluster/name' = '%s';" % self.name)


# The plenaries will only be written if they change.  Technically
# using the refresh_* methods below would result in more work being done
# here than necessary (in calculating all the plenary files) but it's
# better than forgetting to update one of these.  Especially if the data
# changes.
def get_metacluster_plenaries(metacluster):
    plenaries = []
    for p in PlenaryMetaCluster, PlenaryMetaClusterClient, \
             PlenaryMetaClusterData, PlenaryMetaClusterClientData:
        plenaries.append(p(metacluster))
    return plenaries

def get_cluster_plenaries(cluster):
    plenaries = []
    for plenary in PlenaryCluster, PlenaryClusterClient:
        plenaries.append(plenary(cluster))
    return plenaries

def refresh_metacluster_plenaries(metacluster, locked=True):
    plenaries = get_metacluster_plenaries(metacluster)
    count = 0
    try:
        if not locked:
            compileLock()
        for p in plenaries:
            p.write(locked=True)
            count = count + 1
    finally:
        if not locked:
            compileRelease()
    return count

def refresh_cluster_plenaries(cluster, locked=True):
    plenaries = get_cluster_plenaries(cluster)
    count = 0
    try:
        if not locked:
            compileLock()
        for p in plenaries:
            p.write(locked=True)
            count = count + 1
    finally:
        if not locked:
            compileRelease()
    return count


