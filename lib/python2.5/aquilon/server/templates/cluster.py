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


from aquilon.server.templates.base import Plenary
from aquilon.server.templates.machine import PlenaryMachineInfo


class PlenaryMetaCluster(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        lines.append("include { 'cluster/%(name)s/data' };" %
                     self.__dict__)


class PlenaryMetaClusterClient(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/client" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        #lines.append("'/system/cluster/%(name)s' = "
        #    "create('cluster/%(name)s/clientdata');" % self.__dict__)
        lines.append("include { 'cluster/%(name)s/clientdata' };" %
                     self.__dict__)


class PlenaryMetaClusterData(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/data" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        return


class PlenaryMetaClusterClientData(Plenary):
    def __init__(self, dbmetacluster):
        Plenary.__init__(self)
        self.name = dbmetacluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/clientdata" % self.__dict__
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")
        self.clients = [cluster.name for cluster in dbmetacluster.members]

    def body(self, lines):
        lines.append("'name' = '%s';" % self.name);
        lines.append("'clusters' = list(" +
                     ", ".join([("'" + cluster + "'")
                                for cluster in self.clients]) +
                     ");")


class PlenaryCluster(Plenary):
    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.name = dbcluster.name
        self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "cluster/%(metacluster)s/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/config" % self.__dict__
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        lines.append("include { 'cluster/%(metacluster)s/%(name)s/data' };" %
                     self.__dict__)


class PlenaryClusterClient(Plenary):
    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.name = dbcluster.name
        self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "cluster/%(metacluster)s/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/client" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("'/system/cluster' = create('cluster/%(metacluster)s/%(name)s/clientdata');" %
                     self.__dict__)


class PlenaryClusterData(Plenary):
    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.name = dbcluster.name
        self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "cluster/%(metacluster)s/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/data" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        # FIXME: Review and implement or remove.
        return


class PlenaryClusterClientData(Plenary):
    def __init__(self, dbcluster):
        Plenary.__init__(self)
        self.dbcluster = dbcluster
        self.name = dbcluster.name
        self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "cluster/%(metacluster)s/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/clientdata" % self.__dict__
        self.template_type = 'structure'
        self.dir = self.config.get("broker", "plenarydir")

    def body(self, lines):
        lines.append("'name' = '%s';" % self.name)
        lines.append("'metacluster' = create('cluster/%(metacluster)s/clientdata');" %
                     self.__dict__)
        lines.append("'machines' = nlist(")
        for machine in self.dbcluster.machines:
            pmac = PlenaryMachineInfo(machine)
            lines.append("    '%s', create('%s')," % (machine.name,
                                                      pmac.plenary_template))
        lines.append(");")


