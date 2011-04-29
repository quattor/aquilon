# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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


from sqlalchemy.orm import aliased, joinedload_all, contains_eager
from sqlalchemy.sql import or_

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.host import SimpleHostList
from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality,
                                PersonalityGrnMap, HostGrnMap,
                                HostLifecycle, OperatingSystem, Service,
                                ServiceInstance, NasDisk, Disk, Machine, Model,
                                ARecord, Fqdn, DnsDomain, Interface,
                                AddressAssignment, NetworkEnvironment, Network)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byip


class CommandSearchHost(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, hostname, machine, archetype,
               buildstatus, personality, osname, osversion, service, instance,
               model, machine_type, vendor, serial, cluster,
               guest_on_cluster, guest_on_share, member_cluster_share,
               domain, sandbox, branch,
               dns_domain, shortname, mac, ip, networkip, network_environment,
               exact_location, server_of_service, server_of_instance, grn,
               eon_id, fullinfo, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dnsq = session.query(ARecord.ip)
        dnsq = dnsq.join(Fqdn)
        use_dnsq = False
        if hostname:
            (short, dbdns_domain) = parse_fqdn(session, hostname)
            dnsq = dnsq.filter_by(name=short)
            dnsq = dnsq.filter_by(dns_domain=dbdns_domain)
            use_dnsq = True
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)
            dnsq = dnsq.filter_by(dns_domain=dbdns_domain)
            use_dnsq = True
        if shortname:
            dnsq = dnsq.filter_by(name=shortname)
            use_dnsq = True

        use_addrq = False
        addrq = session.query(Interface.id)
        if mac:
            self.deprecated_option("mac", "Please use search machine --mac instead.",
                logger=logger, **arguments)
            addrq = addrq.filter(Interface.mac == mac)
            use_addrq = True
        addrq = addrq.join(AddressAssignment, Network)
        addrq = addrq.filter_by(network_environment=dbnet_env)
        if ip:
            addrq = addrq.filter(AddressAssignment.ip == ip)
            use_addrq = True
        if networkip:
            dbnetwork = get_network_byip(session, networkip, dbnet_env)
            addrq = addrq.filter(AddressAssignment.network == dbnetwork)
            use_addrq = True
        if use_dnsq:
            addrq = addrq.filter(AddressAssignment.ip.in_(dnsq.subquery()))
            use_addrq = True

        q = session.query(Host)

        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            q = q.filter_by(machine=dbmachine)

        # Hardware-specific filters
        q = q.join(Machine)
        q = q.options(contains_eager('machine'))

        dblocation = get_location(session, **arguments)
        if dblocation:
            if exact_location:
                q = q.filter_by(location=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Machine.location_id.in_(childids))

        if model or vendor or machine_type:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            machine_type=machine_type,
                                            compel=True)
            q = q.filter(Machine.model_id.in_(subq))

        if serial:
            self.deprecated_option("serial", "Please use search machine --serial instead.",
                logger=logger, **arguments)
            q = q.filter_by(serial_no=serial)

        if use_addrq:
            q = q.join(Interface)
            q = q.filter(Interface.id.in_(addrq.subquery()))

        # End of hardware-specific filters
        q = q.reset_joinpoint()

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
            PersAlias = aliased(Personality)
            q = q.join(PersAlias).filter_by(name=personality)
            q = q.reset_joinpoint()
        elif archetype:
            PersAlias = aliased(Personality)
            q = q.join(PersAlias).filter_by(archetype=dbarchetype)
            q = q.reset_joinpoint()

        if buildstatus:
            dbbuildstatus = HostLifecycle.get_unique(session, buildstatus,
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
                q = q.join('_services_used')
                q = q.filter_by(service_instance=dbsi)
                q = q.reset_joinpoint()
            else:
                q = q.join('_services_used', 'service_instance')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join('_services_used', 'service_instance')
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        if server_of_service:
            dbserver_service = Service.get_unique(session, server_of_service,
                                                  compel=True)
            if server_of_instance:
                dbssi = get_service_instance(session, dbserver_service,
                                             server_of_instance)
                q = q.join ('_services_provided')
                q = q.filter_by (service_instance=dbssi)
                q = q.reset_joinpoint()
            else:
                q = q.join('_services_provided', 'service_instance')
                q = q.filter_by(service=dbserver_service)
                q = q.reset_joinpoint()
        elif server_of_instance:
            q = q.join(['_services_provided', 'service_instance'])
            q = q.filter_by(name=server_of_instance)
            q = q.reset_joinpoint()

        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            q = q.join('_cluster')
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()
        if guest_on_cluster:
            dbcluster = Cluster.get_unique(session, guest_on_cluster,
                                           compel=True)
            q = q.join('machine', '_cluster')
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()
        if guest_on_share:
            nas_disk_share = Service.get_unique(session, name='nas_disk_share',
                                                compel=True)
            dbshare = ServiceInstance.get_unique(session, name=guest_on_share,
                                                 service=nas_disk_share,
                                                 compel=True)
            NasAlias = aliased(NasDisk)
            q = q.join('machine', 'disks', (NasAlias, NasAlias.id==Disk.id))
            q = q.filter_by(service_instance=dbshare)
            q = q.reset_joinpoint()
        if member_cluster_share:
            nas_disk_share = Service.get_unique(session, name='nas_disk_share',
                                                compel=True)
            dbshare = ServiceInstance.get_unique(session,
                                                 name=member_cluster_share,
                                                 service=nas_disk_share,
                                                 compel=True)
            NasAlias = aliased(NasDisk)
            q = q.join('_cluster', 'cluster', '_machines', 'machine',
                       'disks', (NasAlias, NasAlias.id==Disk.id))
            q = q.filter_by(service_instance=dbshare)
            q = q.reset_joinpoint()

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, autoupdate=False)

            # For some reason, this does not work:
            # q = q.join(Personality).filter_by(or_(Personality.grns.contains(dbgrn),
            #                                       Host.grns.contains(dbgrn)))
            # The generated SQL query contains an implicit inner join instead of
            # an outer join, so if either PersonalityGrnMap or HostGrnMap is
            # empty, there will be no results

            PersAlias = aliased(Personality)
            q = q.join(PersAlias)
            q = q.outerjoin(PersonalityGrnMap)
            q = q.reset_joinpoint()
            q = q.outerjoin(HostGrnMap)
            q = q.reset_joinpoint()
            q = q.filter(or_(PersonalityGrnMap.grn == dbgrn,
                             HostGrnMap.grn == dbgrn))

        if fullinfo:
            return q.all()
        return SimpleHostList(q.all())
