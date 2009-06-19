# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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


from aquilon.server.broker import BrokerCommand, validate_basic, force_int
from aquilon.aqdb.model import EsxCluster, MetaCluster, MetaClusterMember
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.templates.cluster import (PlenaryCluster,
                                              PlenaryClusterClient,
                                              PlenaryClusterData,
                                              PlenaryClusterClientData)
from aquilon.server.templates.base import compileLock, compileRelease


class CommandAddESXCluster(BrokerCommand):

    required_parameters = ["cluster", "metacluster"]

    def render(self, session, cluster, metacluster, archetype, personality,
               max_members, vm_to_host_ratio, comments, **arguments):
        validate_basic("cluster", cluster)

        dblocation = get_location(session, **arguments)
        if not dblocation:
            raise ArgumentError("cluster requires a location constraint")

        existing = EsxCluster.get_unique(session, cluster)
        if existing:
            raise ArgumentError("cluster '%s' already exists" % cluster)

        dbmetacluster = MetaCluster.get_unique(session, metacluster)
        if not dbmetacluster:
            raise NotFoundException("metacluster '%s' not found" % metacluster)

        dbpersonality = get_personality(session, archetype, personality)

        if not max_members:
            max_members = self.config.get("broker",
                                          "esx_cluster_max_members_default")
        max_members = force_int("max_members", max_members)

        if vm_to_host_ratio is None:
            vm_to_host_ratio = self.config.get("broker",
                                               "esx_cluster_vm_to_host_ratio")
        vm_to_host_ratio = force_int("vm_to_host_ratio", vm_to_host_ratio)

        dbcluster = EsxCluster(name=cluster,
                               location_constraint=dblocation,
                               personality=dbpersonality,
                               max_hosts=max_members,
                               vm_to_host_ratio=vm_to_host_ratio,
                               comments=comments)
        session.add(dbcluster)

        try:
            # AQDB checks the max_members attribute.
            dbmcm = MetaClusterMember(metacluster=dbmetacluster,
                                      cluster=dbcluster)
            session.add(dbmcm)
        except ValueError, e:
            raise ArgumentError(e.message)

        session.flush()
        session.refresh(dbcluster)

        plenaries = []
        # FIXME: Probably also need to re-write some/all of the MetaCluster
        # plenary files.
        for p in PlenaryCluster, PlenaryClusterClient, PlenaryClusterData, \
                 PlenaryClusterClientData:
            plenaries.append(p(dbcluster))
        try:
            compileLock()
            for p in plenaries:
                p.write(locked=True)
        finally:
            compileRelease()

        return


