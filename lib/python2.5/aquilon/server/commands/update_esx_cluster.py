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
from aquilon.aqdb.model import EsxCluster
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.templates.cluster import (PlenaryCluster,
                                              PlenaryClusterClient,
                                              PlenaryClusterData,
                                              PlenaryClusterClientData)
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.host import PlenaryHost


class CommandUpdateESXCluster(BrokerCommand):

    required_parameters = [ "cluster" ]

    def render(self, session, cluster, archetype, personality,
               max_members, vm_to_host_ratio, comments, **arguments):
        dbcluster = session.query(EsxCluster).filter_by(name=cluster).first()
        if not dbcluster:
            raise NotFoundException("cluster '%s' not found" % cluster)

        cluster_updated = False

        dblocation = get_location(session, **arguments)
        if dblocation:
            # FIXME: Need to check that cluster members have this location.
            dbcluster.location = dblocation
            cluster_updated = True

        if personality:
            if not archetype:
                archetype = dbcluster.personality.archetype.name
            dbpersonality = get_personality(session, archetype, personality)
            # It would be nice to reconfigure all the hosts here.  That
            # would take some refactoring of the present code.
            for dbhost in dbcluster.members:
                invalid_hosts = []
                if dbhost.personality != dbpersonality:
                    invalid_hosts.append(dbhost)
                if invalid_hosts:
                    raise ArgumentError("Cannot change cluster personality "
                                        "while containing members of a "
                                        "different personality: %s" %
                                        invalid_hosts)
            dbcluster.personality = dbpersonality
            cluster_updated = True

        max_members = force_int("max_members", max_members)
        if max_members is not None:
            if max_members < len(dbcluster.members):
                raise ArgumentError("Could not set cluster max_members to %s "
                                    "as value already exceeded (%s)." %
                                    (max_members, len(dbcluster.members)))
            dbcluster.max_hosts = max_members
            cluster_updated = True

        vm_to_host_ratio = force_int("vm_to_host_ratio", vm_to_host_ratio)
        if vm_to_host_ratio is not None:
            # FIXME: Enforce that this is not being exceeded.
            dbcluster.vm_to_host_ratio = vm_to_host_ratio
            cluster_updated = True

        if comments is not None:
            dbcluster.comments = comments
            cluster_updated = True

        if not cluster_updated:
            return

        session.add(dbcluster)
        session.flush()
        # FIXME: May not need to re-write all the plenary templates.
        plenaries = []
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


