# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq search host`."""

from sqlalchemy.orm import aliased, contains_eager
from sqlalchemy.sql import and_, or_

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality,
                                PersonalityGrnMap, HostGrnMap, HostLifecycle,
                                OperatingSystem, Service, ServiceInstance,
                                Share, VirtualNasDisk, Disk, Machine, Model,
                                DnsRecord, ARecord, Fqdn, DnsDomain, Interface,
                                AddressAssignment, NetworkEnvironment, Network,
                                MetaCluster, VirtualMachine, ClusterResource,
                                HardwareEntity, HostEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.list import StringAttributeList
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byip
from aquilon.worker.dbwrappers.user_principal import get_user_principal


class CommandSearchHost(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, hostname, machine, archetype,
               buildstatus, personality, host_environment, osname, osversion,
               service, instance, model, machine_type, vendor, serial, cluster,
               guest_on_cluster, guest_on_share, member_cluster_share,
               domain, sandbox, branch, sandbox_owner,
               dns_domain, shortname, mac, ip, networkip, network_environment,
               exact_location, server_of_service, server_of_instance, grn,
               eon_id, fullinfo, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)

        q = session.query(Host)

        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            q = q.filter_by(hardware_entity=dbmachine)

        # Add the machine definition and the primary name. Use aliases to make
        # sure the end result will be ordered by primary name.
        PriDns = aliased(DnsRecord)
        PriFqdn = aliased(Fqdn)
        PriDomain = aliased(DnsDomain)
        q = q.join(HardwareEntity,
                   (PriDns, PriDns.id == Machine.primary_name_id),
                   (PriFqdn, PriDns.fqdn_id == PriFqdn.id),
                   (PriDomain, PriFqdn.dns_domain_id == PriDomain.id))
        q = q.order_by(PriFqdn.name, PriDomain.name)
        q = q.options(contains_eager('hardware_entity'),
                      contains_eager('hardware_entity.primary_name', alias=PriDns),
                      contains_eager('hardware_entity.primary_name.fqdn', alias=PriFqdn),
                      contains_eager('hardware_entity.primary_name.fqdn.dns_domain',
                                     alias=PriDomain))
        q = q.reset_joinpoint()

        # Hardware-specific filters
        dblocation = get_location(session, **arguments)
        if dblocation:
            if exact_location:
                q = q.filter(HardwareEntity.location == dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(HardwareEntity.location_id.in_(childids))

        if model or vendor or machine_type:
            subq = Model.get_matching_query(session, name=model, vendor=vendor,
                                            model_type=machine_type,
                                            compel=True)
            q = q.filter(HardwareEntity.model_id.in_(subq))

        if serial:
            self.deprecated_option("serial",
                                   "Please use search machine --serial instead.",
                                   logger=logger, **arguments)
            q = q.filter(HardwareEntity.serial_no == serial)

        # DNS IP address related filters
        if mac or ip or networkip or hostname or dns_domain or shortname:
            # Inner joins are cheaper than outer joins, so make some effort to
            # use inner joins when possible
            if mac or ip or networkip:
                q = q.join(Interface)
            else:
                q = q.outerjoin(Interface)
            if ip or networkip:
                q = q.join(AddressAssignment, Network, from_joinpoint=True)
            else:
                q = q.outerjoin(AddressAssignment, Network, from_joinpoint=True)

            if mac:
                self.deprecated_option("mac", "Please use search machine "
                                       "--mac instead.", logger=logger,
                                       **arguments)
                q = q.filter(Interface.mac == mac)
            if ip:
                q = q.filter(AddressAssignment.ip == ip)
                q = q.filter(Network.network_environment == dbnet_env)
            if networkip:
                dbnetwork = get_network_byip(session, networkip, dbnet_env)
                q = q.filter(AddressAssignment.network == dbnetwork)

            dbdns_domain = None
            if hostname:
                (shortname, dbdns_domain) = parse_fqdn(session, hostname)
            if dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

            if shortname or dbdns_domain:
                ARecAlias = aliased(ARecord)
                ARecFqdn = aliased(Fqdn)

                q = q.outerjoin((ARecAlias,
                                 and_(ARecAlias.ip == AddressAssignment.ip,
                                      ARecAlias.network_id == AddressAssignment.network_id)),
                                (ARecFqdn, ARecAlias.fqdn_id == ARecFqdn.id))
                if shortname:
                    q = q.filter(or_(ARecFqdn.name == shortname,
                                     PriFqdn.name == shortname))
                if dbdns_domain:
                    q = q.filter(or_(ARecFqdn.dns_domain == dbdns_domain,
                                     PriFqdn.dns_domain == dbdns_domain))
            q = q.reset_joinpoint()

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     branch=branch)
        if sandbox_owner:
            dbauthor = get_user_principal(session, sandbox_owner)

        if dbbranch:
            q = q.filter_by(branch=dbbranch)
        if dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        # Just do the lookup here, filtering will happen later
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        else:
            dbarchetype = None

        if archetype or personality or host_environment:
            PersAlias = aliased(Personality)
            q = q.join(PersAlias)

            if archetype:
                q = q.filter_by(archetype=dbarchetype)
            if personality:
                subq = Personality.get_matching_query(session, name=personality,
                                                      archetype=dbarchetype,
                                                      compel=True)
                q = q.filter(PersAlias.id.in_(subq))
            if host_environment:
                dbhost_env = HostEnvironment.get_instance(session,
                                                          host_environment)
                q = q.filter_by(host_environment=dbhost_env)

            q = q.reset_joinpoint()

        if buildstatus:
            dbbuildstatus = HostLifecycle.get_instance(session, buildstatus)
            q = q.filter_by(status=dbbuildstatus)

        if osname or osversion:
            subq = OperatingSystem.get_matching_query(session, name=osname,
                                                      version=osversion,
                                                      archetype=dbarchetype,
                                                      compel=True)
            q = q.filter(Host.operating_system_id.in_(subq))

        if service:
            dbservice = Service.get_unique(session, service, compel=True)
            if instance:
                dbsi = ServiceInstance.get_unique(session, service=dbservice,
                                                  name=instance, compel=True)
                q = q.filter(Host.services_used.contains(dbsi))
            else:
                q = q.join('services_used')
                q = q.filter_by(service=dbservice)
                q = q.reset_joinpoint()
        elif instance:
            q = q.join('services_used')
            q = q.filter_by(name=instance)
            q = q.reset_joinpoint()

        if server_of_service:
            dbserver_service = Service.get_unique(session, server_of_service,
                                                  compel=True)
            if server_of_instance:
                dbsi = ServiceInstance.get_unique(session,
                                                  service=dbserver_service,
                                                  name=server_of_instance,
                                                  compel=True)
                q = q.join('services_provided')
                q = q.filter_by(service_instance=dbsi)
                q = q.reset_joinpoint()
            else:
                q = q.join('services_provided', 'service_instance')
                q = q.filter_by(service=dbserver_service)
                q = q.reset_joinpoint()
        elif server_of_instance:
            q = q.join('services_provided', 'service_instance')
            q = q.filter_by(name=server_of_instance)
            q = q.reset_joinpoint()

        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if isinstance(dbcluster, MetaCluster):
                q = q.join('_cluster', 'cluster', '_metacluster')
                q = q.filter_by(metacluster=dbcluster)
            else:
                q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()

        if guest_on_cluster:
            # TODO: this does not handle metaclusters according to Wes
            dbcluster = Cluster.get_unique(session, guest_on_cluster,
                                           compel=True)
            q = q.join(Host.hardware_entity.of_type(Machine),
                       VirtualMachine, ClusterResource)
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()

        if guest_on_share:
            v2shares = session.query(Share.id).filter_by(name=guest_on_share)
            if not v2shares.count():
                raise NotFoundException("No shares found with name {0}."
                                        .format(guest_on_share))

            NasAlias = aliased(VirtualNasDisk)
            q = q.join(Host.hardware_entity.of_type(Machine),
                       Disk, (NasAlias, NasAlias.id == Disk.id))
            q = q.filter(NasAlias.share_id.in_(v2shares.subquery()))
            q = q.reset_joinpoint()

        if member_cluster_share:
            v2shares = session.query(Share.id).filter_by(name=member_cluster_share)
            if not v2shares.count():
                raise NotFoundException("No shares found with name {0}."
                                        .format(guest_on_share))

            NasAlias = aliased(VirtualNasDisk)
            q = q.join('_cluster', 'cluster', 'resholder', VirtualMachine,
                       'machine', 'disks', (NasAlias, NasAlias.id == Disk.id))
            q = q.filter(NasAlias.share_id.in_(v2shares.subquery()))
            q = q.reset_joinpoint()

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, autoupdate=False)

            persq = session.query(Personality.id)
            persq = persq.outerjoin(PersonalityGrnMap)
            persq = persq.filter(or_(Personality.owner_eon_id == dbgrn.eon_id,
                                     PersonalityGrnMap.eon_id == dbgrn.eon_id))
            q = q.outerjoin(HostGrnMap)
            q = q.filter(or_(Host.owner_eon_id == dbgrn.eon_id,
                             HostGrnMap.eon_id == dbgrn.eon_id,
                             Host.personality_id.in_(persq.subquery())))
            q = q.reset_joinpoint()

        if fullinfo:
            return q.all()
        return StringAttributeList(q.all(), "fqdn")
