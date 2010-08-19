# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq search host`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.model import (Host, Cluster, Domain, Archetype, Personality,
                                HostLifecycle,
                                OperatingSystem, Service, Machine, Model)
from aquilon.server.dbwrappers.system import search_system_query
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.dbwrappers.branch import get_branch_and_author
from aquilon.server.dbwrappers.location import get_location


class CommandSearchHost(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, hostname, machine, archetype,
               buildstatus, personality, osname, osversion, service, instance,
               model, machine_type, vendor, serial, cluster,
               domain, sandbox, branch,
               fullinfo, **arguments):
        if hostname:
            arguments['fqdn'] = hostname
        q = search_system_query(session, Host, **arguments)
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            q = q.filter_by(machine=dbmachine)

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     branch=branch)
        if dbbranch:
            q = q.filter_by(branch=dbbranch)
        if dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        if archetype:
            # Added to the searches as appropriate below.
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if personality and archetype:
            dbpersonality = Personality.get_unique(session,
                                                   archetype=dbarchetype,
                                                   name=personality,
                                                   compel=True)
            q = q.filter_by(personality=dbpersonality)
        elif personality:
            q = q.join('personality').filter_by(name=personality)
            q = q.reset_joinpoint()
        elif archetype:
            q = q.join('personality').filter_by(archetype=dbarchetype)
            q = q.reset_joinpoint()

        if buildstatus:
            dbbuildstatus = HostLifecycleget_unique(session, buildstatus,
                                                    compel=True)
            q = q.filter_by(status=dbbuildstatus)

        if osname and osversion and archetype:
            # archetype was already resolved above
            dbos = OperatingSystem.get_unique(session, name=osname,
                                              version=osversion,
                                              archetype=dbarchetype,
                                              compel=True)
            q = q.filter_by(operating_system=dbos)
        elif osname or osversion:
            q = q.join('operating_system')
            if osname:
                q = q.filter_by(name=osname)
            if osversion:
                q = q.filter_by(version=osversion)
            q = q.reset_joinpoint()

        if service:
            dbservice = Service.get_unique(session, service, compel=True)
            if instance:
                dbsi = get_service_instance(session, dbservice, instance)
                q = q.join('build_items')
                q = q.filter_by(service_instance=dbsi)
                q = q.reset_joinpoint()
            else:
                q = q.join('build_items', 'service_instance')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join(['build_items', 'service_instance'])
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        dblocation = get_location(session, **arguments)
        if dblocation:
            q = q.join(['machine'])
            if arguments.get('exact_location'):
                q = q.filter_by(location=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Machine.location_id.in_(childids))
            q = q.reset_joinpoint()
        if model or vendor or machine_type:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type=machine_type,
                                            compel=True)
            q = q.join(['machine'])
            q = q.filter(Machine.model_id.in_(subq))
            q = q.reset_joinpoint()
        if serial:
            q = q.join(['machine'])
            q = q.filter_by(serial_no=serial)
            q = q.reset_joinpoint()
        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            q = q.join('_cluster')
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()
        if fullinfo:
            return q.all()
        return SimpleSystemList(q.all())
