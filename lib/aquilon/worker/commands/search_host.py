# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from sqlalchemy.orm import (aliased, contains_eager, joinedload, subqueryload,
                            undefer)
from sqlalchemy.sql import and_, or_, null

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality,
                                PersonalityStage, PersonalityGrnMap,
                                HostGrnMap, HostLifecycle, OperatingSystem,
                                ServiceInstance, ServiceInstanceServer, Share,
                                VirtualDisk, Machine, Model, DnsRecord, ARecord,
                                Fqdn, DnsDomain, Interface, AddressAssignment,
                                NetworkEnvironment, Network, MetaCluster,
                                VirtualMachine, ClusterResource, HardwareEntity,
                                HostEnvironment, User, Branch, Feature,
                                FeatureLink)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.dbwrappers.host import preload_machine_data
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byip


class CommandSearchHost(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, hostname, machine, archetype, buildstatus,
               personality, personality_stage, host_environment, osname, osversion,
               service, instance, model, machine_type, vendor, serial, cluster,
               cluster_archetype, cluster_personality,
               guest_on_cluster, guest_on_share, member_cluster_share, domain,
               sandbox, branch, sandbox_author, dns_domain, shortname, mac, ip,
               networkip, network_environment, exact_location, metacluster,
               server_of_service, server_of_instance, grn, eon_id, fullinfo,
               orphaned, style, **arguments):
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
        if mac or ip or networkip or hostname or dns_domain or \
           shortname or network_environment:
            # Inner joins are cheaper than outer joins, so make some effort to
            # use inner joins when possible
            if mac or ip or networkip or network_environment:
                q = q.join(Interface, aliased=True)
            else:
                q = q.outerjoin(Interface, aliased=True)
            if mac:
                self.deprecated_option("mac", "Please use search machine "
                                       "--mac instead.", logger=logger,
                                       **arguments)
                q = q.filter(Interface.mac == mac)

            AAlias = aliased(AddressAssignment)

            if ip or networkip or network_environment:
                q = q.join(AAlias, from_joinpoint=True)
            else:
                q = q.outerjoin(AAlias, from_joinpoint=True)

            if ip:
                q = q.filter(AAlias.ip == ip)
            elif networkip:
                dbnetwork = get_network_byip(session, networkip, dbnet_env)
                q = q.filter(AAlias.network == dbnetwork)
            elif network_environment:
                q = q.join(AAlias.network, aliased=True)
                q = q.filter(Network.network_environment == dbnet_env)

            dbdns_domain = None
            if hostname:
                (shortname, dbdns_domain) = parse_fqdn(session, hostname)
            if dns_domain:
                dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

            if shortname or dbdns_domain:
                ARecAlias = aliased(ARecord)
                ARecFqdn = aliased(Fqdn)

                q = q.outerjoin((ARecAlias,
                                 and_(ARecAlias.ip == AAlias.ip,
                                      ARecAlias.network_id == AAlias.network_id)),
                                (ARecFqdn, ARecAlias.fqdn_id == ARecFqdn.id))
                if shortname and dbdns_domain:
                    q = q.filter(or_(and_(ARecFqdn.name == shortname,
                                          ARecFqdn.dns_domain == dbdns_domain),
                                     and_(PriFqdn.name == shortname,
                                          PriFqdn.dns_domain == dbdns_domain)))
                elif shortname:
                    q = q.filter(or_(ARecFqdn.name == shortname,
                                     PriFqdn.name == shortname))
                elif dbdns_domain:
                    q = q.filter(or_(ARecFqdn.dns_domain == dbdns_domain,
                                     PriFqdn.dns_domain == dbdns_domain))
            q = q.reset_joinpoint()

        dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                                   sandbox=sandbox,
                                                   branch=branch, orphaned=orphaned)
        if sandbox_author:
            dbauthor = User.get_unique(session, sandbox_author, compel=True)

        if dbbranch:
            q = q.filter_by(branch=dbbranch)

        if orphaned:
            q = q.join(Branch)
            q = q.filter(Branch.branch_type == "sandbox")
            q = q.filter(Host.sandbox_author_id == null())
        elif dbauthor:
            q = q.filter_by(sandbox_author=dbauthor)

        # Just do the lookup here, filtering will happen later
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        else:
            dbarchetype = None

        if archetype or personality or host_environment:
            q = q.join(PersonalityStage, aliased=True)
            if personality_stage:
                Personality.force_valid_stage(personality_stage)
                q = q.filter_by(name=personality_stage)
            if personality:
                subq = Personality.get_matching_query(session, name=personality,
                                                      archetype=dbarchetype,
                                                      compel=True)
                q = q.filter(PersonalityStage.personality_id.in_(subq))

            if archetype or host_environment:
                q = q.join(Personality, aliased=True, from_joinpoint=True)
                if archetype:
                    q = q.filter_by(archetype=dbarchetype)
                if host_environment:
                    dbhost_env = HostEnvironment.get_instance(session,
                                                              host_environment)
                    q = q.filter_by(host_environment=dbhost_env)

            q = q.reset_joinpoint()

        if feature:
            q = q.join(Personality).join(FeatureLink).join(Feature)
            q = q.filter_by(name=feature)
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

        if service or instance:
            subq = ServiceInstance.get_matching_query(session, name=instance,
                                                      service=service,
                                                      compel=True)
            q = q.join(Host.services_used, aliased=True)
            q = q.filter(ServiceInstance.id.in_(subq))
            q = q.reset_joinpoint()

        if server_of_service or server_of_instance:
            subq = ServiceInstance.get_matching_query(session,
                                                      name=server_of_instance,
                                                      service=server_of_service,
                                                      compel=True)
            q = q.join(Host.services_provided, aliased=True)
            q = q.filter(ServiceInstanceServer.service_instance_id.in_(subq))
            q = q.reset_joinpoint()

        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            # TODO: disallow metaclusters here
            if isinstance(dbcluster, MetaCluster):
                q = q.join('_cluster', 'cluster', aliased=True)
                q = q.filter_by(metacluster=dbcluster)
            else:
                q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()

        if cluster_archetype:
            dbarchetype = Archetype.get_unique(session, cluster_archetype, compel=True)
            q = q.join('_cluster', 'cluster', 'personality_stage', 'personality', aliased=True)
            q = q.filter_by(archetype=dbarchetype)
            q = q.reset_joinpoint()

        if cluster_personality:
            dbpersonality = Personality.get_unique(session, name=cluster_personality, archetype=cluster_archetype, compel=True)
            q = q.join('_cluster', 'cluster', 'personality_stage', aliased=True)
            q = q.filter_by(personality=dbpersonality)
            q = q.reset_joinpoint()

        if metacluster:
            dbmeta = MetaCluster.get_unique(session, metacluster, compel=True)
            q = q.join('_cluster', 'cluster', aliased=True)
            q = q.filter_by(metacluster=dbmeta)
            q = q.reset_joinpoint()

        if guest_on_cluster:
            # TODO: this does not handle metaclusters according to Wes
            dbcluster = Cluster.get_unique(session, guest_on_cluster,
                                           compel=True)
            q = q.join(Host.hardware_entity.of_type(Machine),
                       VirtualMachine, ClusterResource, aliased=True)
            q = q.filter_by(cluster=dbcluster)
            q = q.reset_joinpoint()

        if guest_on_share:
            v2shares = session.query(Share.id).filter_by(name=guest_on_share)
            if not v2shares.count():
                raise NotFoundException("No shares found with name {0}."
                                        .format(guest_on_share))

            q = q.join(Host.hardware_entity.of_type(Machine),
                       Machine.disks.of_type(VirtualDisk), aliased=True)
            q = q.filter(VirtualDisk.backing_store_id.in_(v2shares.subquery()))
            q = q.reset_joinpoint()

        if member_cluster_share:
            v2shares = session.query(Share.id).filter_by(name=member_cluster_share)
            if not v2shares.count():
                raise NotFoundException("No shares found with name {0}."
                                        .format(guest_on_share))

            q = q.join('_cluster', 'cluster', ClusterResource, VirtualMachine,
                       Machine, Machine.disks.of_type(VirtualDisk), aliased=True)
            q = q.filter(VirtualDisk.backing_store_id.in_(v2shares.subquery()))
            q = q.reset_joinpoint()

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, autoupdate=False,
                               usable_only=False)

            persq = session.query(PersonalityStage.id)
            persq = persq.join(Personality)
            persq = persq.outerjoin(PersonalityGrnMap)
            persq = persq.filter(or_(Personality.owner_eon_id == dbgrn.eon_id,
                                     PersonalityGrnMap.eon_id == dbgrn.eon_id))

            q = q.outerjoin(Host.grns, aliased=True)
            q = q.filter(or_(Host.owner_eon_id == dbgrn.eon_id,
                             HostGrnMap.eon_id == dbgrn.eon_id,
                             Host.personality_stage_id.in_(persq.subquery())))
            q = q.reset_joinpoint()

        if fullinfo or style != "raw":
            q = q.options(joinedload('personality_stage'),
                          joinedload('personality_stage.personality'),
                          undefer('personality_stage.personality.archetype.comments'),
                          subqueryload('personality_stage.grns'),
                          subqueryload('grns'),
                          subqueryload('services_used'),
                          subqueryload('services_provided'),
                          joinedload('resholder'),
                          subqueryload('resholder.resources'),
                          joinedload('_cluster'),
                          subqueryload('_cluster.cluster'),
                          joinedload('hardware_entity.model'),
                          subqueryload('hardware_entity.interfaces'),
                          subqueryload('hardware_entity.interfaces.assignments'),
                          subqueryload('hardware_entity.interfaces.assignments.dns_records'),
                          joinedload('hardware_entity.interfaces.assignments.network'),
                          joinedload('hardware_entity.location'),
                          subqueryload('hardware_entity.location.parents'))
            dbhosts = q.all()
            preload_machine_data(session, dbhosts)
            return dbhosts

        return StringAttributeList(q.all(), "fqdn")
