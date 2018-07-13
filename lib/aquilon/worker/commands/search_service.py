# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015,2018  Contributor
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
"""Contains the logic for `aq search service`."""

from sqlalchemy.orm import (joinedload, subqueryload, undefer, contains_eager,
                            aliased)
from sqlalchemy.sql import or_, and_

from aquilon.aqdb.model import (Service, ServiceInstance, ServiceInstanceServer,
                                HardwareEntity, Host, Cluster, MetaCluster)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.dbwrappers.location import get_location


class CommandSearchService(BrokerCommand):

    def render(self, session, service, instance,
               server_hostname, server_cluster, server_metacluster,
               server_exact_location,
               client_hostname, client_cluster, client_metacluster,
               has_clients, client_exact_location,
               fullinfo, style, **arguments):
        q = session.query(ServiceInstance)
        if instance:
            q = q.filter_by(name=instance)

        if service:
            dbservice = Service.get_unique(session, service, compel=True)
            q = q.filter_by(service=dbservice)

        # We need the explicit join for ordering
        q = q.join(Service)
        q = q.options(contains_eager('service'))
        q = q.reset_joinpoint()

        dbserver_loc = get_location(
            session, locfunc=lambda x: 'server_{}'.format(x), **arguments)
        dbclient_loc = get_location(
            session, locfunc=lambda x: 'client_{}'.format(x), **arguments)

        if server_hostname or server_cluster or server_metacluster:
            q = q.join(ServiceInstance.servers, aliased=True)

            if server_hostname:
                dbhost = hostname_to_host(session, server_hostname)
                q = q.filter_by(host=dbhost)

            if server_cluster:
                dbcluster = Cluster.get_unique(session, server_cluster,
                                               compel=True)
                q = q.filter_by(cluster=dbcluster)

            if server_metacluster:
                dbmeta = MetaCluster.get_unique(session, server_metacluster,
                                                compel=True)
                q = q.filter_by(cluster=dbmeta)

            q = q.reset_joinpoint()

        if dbserver_loc:
            SISAlias = aliased(ServiceInstanceServer)
            ClAlias = aliased(Cluster)
            HostAlias = aliased(Host)
            HwAlias = aliased(HardwareEntity)
            HostHw = session.query(HostAlias.hardware_entity_id,
                                   HwAlias.location_id).join(HwAlias).subquery()

            q = q.join(SISAlias)
            q = q.outerjoin(ClAlias,
                            ClAlias.id == SISAlias.cluster_id)
            q = q.outerjoin((HostHw,
                             HostHw.c.hardware_entity_id == SISAlias.host_id))

            if server_exact_location:
                q = q.filter(or_(ClAlias.location_constraint == dbserver_loc,
                                 HostHw.c.location_id == dbserver_loc.id))
            else:
                childids = dbserver_loc.offspring_ids()
                q = q.filter(or_(ClAlias.location_constraint_id.in_(childids),
                                 HostHw.c.location_id.in_(childids)))

            q = q.reset_joinpoint()

        if client_hostname:
            dbhost = hostname_to_host(session, client_hostname)
            q = q.filter(ServiceInstance.clients.contains(dbhost))

        if client_cluster:
            dbcluster = Cluster.get_unique(session, client_cluster, compel=True)
            q = q.filter(ServiceInstance.cluster_clients.contains(dbcluster))

        if client_metacluster:
            dbmeta = MetaCluster.get_unique(session, client_metacluster,
                                            compel=True)
            q = q.filter(ServiceInstance.cluster_clients.contains(dbmeta))

        if dbclient_loc:
            ClAlias = aliased(Cluster)
            HostAlias = aliased(Host)
            HwAlias = aliased(HardwareEntity)
            HostHw = session.query(HostAlias.hardware_entity_id,
                                   HwAlias.location_id).join(HwAlias).subquery()

            # TODO: outerjoin is expensive here
            q = q.outerjoin(HostHw, ServiceInstance.clients)
            q = q.outerjoin(ClAlias, ServiceInstance.cluster_clients)

            if client_exact_location:
                q = q.filter(or_(ClAlias.location_constraint == dbclient_loc,
                                 HostHw.c.location_id == dbclient_loc.id))
            else:
                childids = dbclient_loc.offspring_ids()
                q = q.filter(or_(ClAlias.location_constraint_id.in_(childids),
                                 HostHw.c.location_id.in_(childids)))

            q = q.reset_joinpoint()

        if has_clients is True:
            q = q.filter(or_(ServiceInstance.clients.any(),
                             ServiceInstance.cluster_clients.any()))
        elif has_clients is False:
            q = q.filter(and_(~ServiceInstance.clients.any(),
                              ~ServiceInstance.cluster_clients.any()))

        q = q.order_by(Service.name, ServiceInstance.name)

        if fullinfo or style != 'raw':
            q = q.options(undefer('_client_count'),
                          subqueryload('servers'),
                          joinedload('servers.host'),
                          joinedload('servers.host.hardware_entity'),
                          subqueryload('service_map'),
                          joinedload('service_map.location'),
                          joinedload('service_map.network'),
                          joinedload('service_map.personality'))
            return q.all()
        else:
            return StringAttributeList(q.all(), "qualified_name")
