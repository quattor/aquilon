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
"""Contains the logic for `aq search machine`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.formats.hardware_entity import SimpleHardwareEntityList
from aquilon.aqdb.model import Machine, Vendor, Cpu, Cluster
from aquilon.server.dbwrappers.hardware_entity import (
    search_hardware_entity_query)


class CommandSearchMachine(BrokerCommand):

    required_parameters = []

    def render(self, session, name, cpuname, cpuvendor, cpuspeed, cpucount,
               memory, cluster, fullinfo, **arguments):
        q = search_hardware_entity_query(session, Machine, **arguments)
        if name:
            q = q.filter_by(name=name)
        if cpuname and cpuvendor and cpuspeed:
            dbvendor = Vendor.get_unique(session, cpuvendor)
            if not dbvendor:
                raise ArgumentError("Vendor '%s' not found." % cpuvendor)
            cpuspeed = force_int("cpuspeed", cpuspeed)
            dbcpu = Cpu.get_unique(session, vendor_id=dbvendor.id,
                                   name=cpuname, speed=cpuspeed)
            if not dbcpu:
                raise ArgumentError("CPU vendor='%s' name='%s' speed='%s' "
                                    "not found." %
                                    (dbvendor.name, cpuname, cpuspeed))
            q = q.filter_by(cpu=dbcpu)
        elif cpuname or cpuvendor or cpuspeed:
            q = q.join('cpu')
            if cpuvendor:
                dbvendor = Vendor.get_unique(session, cpuvendor)
                if not dbvendor:
                    raise ArgumentError("Vendor '%s' not found." % cpuvendor)
                q = q.filter_by(vendor=dbvendor)
            if cpuspeed:
                cpuspeed = force_int("cpuspeed", cpuspeed)
                q = q.filter_by(speed=cpuspeed)
            if cpuname:
                q = q.filter_by(name=cpuname)
            q = q.reset_joinpoint()
        if cpucount:
            cpucount = force_int("cpucount", cpucount)
            q = q.filter_by(cpu_quantity=cpucount)
        if memory:
            memory = force_int("memory", memory)
            q = q.filter_by(memory=memory)
        if cluster:
            dbcluster = Cluster.get_unique(session, cluster)
            if not dbcluster:
                raise ArgumentError("Cluster '%s' not found." % cluster)
            q = q.join('_cluster')
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()
        if fullinfo:
            return q.all()
        return SimpleHardwareEntityList(q.all())


