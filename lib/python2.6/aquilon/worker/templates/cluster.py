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


import logging

from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.panutils import pan, StructureTemplate
from aquilon.worker.locks import CompileKey

LOGGER = logging.getLogger(__name__)


class PlenaryCluster(PlenaryCollection):
    """
    A facade for the variety of PlenaryCluster subsidiary files
    """
    def __init__(self, dbcluster, logger=LOGGER):
        PlenaryCollection.__init__(self, logger=LOGGER)
        self.plenaries.append(PlenaryClusterObject(dbcluster, logger=logger))
        self.plenaries.append(PlenaryClusterClient(dbcluster, logger=logger))


class PlenaryClusterObject(Plenary):
    """
    A cluster has its own output profile, so the plenary cluster template
    is an object template that includes the data about which machines
    are contained inside the cluster (via an include of the clusterdata plenary)
    """

    def __init__(self, dbcluster, logger=LOGGER):
        Plenary.__init__(self, dbcluster, logger=logger)
        self.template_type = 'object'
        self.dbcluster = dbcluster
        self.name = dbcluster.name
        self.metacluster = "global"
        if dbcluster.metacluster:
            self.metacluster = dbcluster.metacluster.name
        self.plenary_core = "clusters"
        self.plenary_template = "%(plenary_core)s/%(name)s" % self.__dict__
        self.dir = self.config.get("broker", "builddir") + \
                    "/domains/%s/profiles" % dbcluster.branch.name

    def get_key(self):
        return CompileKey(domain=self.dbcluster.branch.name,
                          profile=self.plenary_template, logger=self.logger)

    def body(self, lines):
        arcdir = self.dbcluster.personality.archetype.name
        lines.append("# this is an %s cluster, so all templates "
                     "should be sourced from there" % arcdir)
        lines.append("variable LOADPATH = %s;" % pan([arcdir]))
        lines.append("")

        lines.append("include { 'pan/units' };")
        lines.append("")
        lines.append('"/system/cluster/name" = %s;' % pan(self.name))
        lines.append('"/system/cluster/type" = %s;' %
                        pan(self.dbcluster.cluster_type))
        lines.append("")
        lines.append("include { 'archetype/cluster/base' };")
        fname = "body_%s" % self.dbcluster.cluster_type
        if hasattr(self, fname):
            getattr(self, fname)(lines)
        lines.append("")
        lines.append("include { 'personality/%s/config' };" %
                     self.dbcluster.personality.name)
        lines.append("")
        lines.append("include { 'archetype/cluster/final' };")

    def body_esx(self, lines):
        if self.metacluster:
            lines.append('"/system/metacluster/name" = %s;' %
                         pan(self.metacluster))
        campus = self.dbcluster.location_constraint.campus
        if campus:
            lines.append('"/system/cluster/campus" = %s;' % pan(campus.name))
        lines.append('"/system/cluster/ratio" = %s;' % pan([
                            self.dbcluster.vm_count,
                            self.dbcluster.host_count]))
        lines.append('"/system/cluster/max_hosts" = %d;' %
                     self.dbcluster.max_hosts)
        lines.append('"/system/cluster/down_hosts_threshold" = %d;' %
                     self.dbcluster.down_hosts_threshold)
        lines.append('')
        # Only use system names here to avoid circular dependencies.
        # Other templates that needs to look up the underlying values use:
        # foreach(idx; host; value("/system/cluster/members")) {
        #     v = value("//" + host + "/system/foo/bar/baz");
        # );
        lines.append('"/system/cluster/members" = %s;' %
                     pan([member.fqdn for member in self.dbcluster.hosts]))
        lines.append('')
        machines = {}
        for machine in self.dbcluster.machines:
            if not machine.interfaces or not machine.disks:
                # Do not bother creating entries for VMs that are incomplete.
                continue
            pmac = PlenaryMachineInfo(machine)
            macdesc = {'hardware': StructureTemplate(pmac.plenary_template)}

            # One day we may get to the point where this will be required.
            if (machine.host):
                # we fill this in manually instead of just assigning
                # 'system' = value("//hostname/system")
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
        lines.append('"/system/cluster/machines" = %s;' % pan(machines))

        for servinst in self.dbcluster.service_bindings:
            lines.append("include { 'service/%s/%s/client/config' };" % \
                         (servinst.service.name, servinst.name))


class PlenaryClusterClient(Plenary):
    """
    A host that is a member of a cluster will include the cluster client
    plenary template. This just names the cluster and nothing more.
    """
    def __init__(self, dbcluster, logger=LOGGER):
        Plenary.__init__(self, dbcluster, logger=logger)
        self.name = dbcluster.name
        self.plenary_core = "cluster/%(name)s" % self.__dict__
        self.plenary_template = "%(plenary_core)s/client" % self.__dict__
        self.template_type = ''
        self.dir = self.config.get("broker", "plenarydir")

    def get_key(self):
        # This takes a domain lock because it could affect all clients...
        return CompileKey(domain=self.dbobj.branch.name, logger=self.logger)

    def body(self, lines):
        lines.append('"/system/cluster/name" = %s;' % pan(self.name))
