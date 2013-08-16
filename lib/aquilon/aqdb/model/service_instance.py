# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
""" see class.__doc__ for description """

from collections import defaultdict
from datetime import datetime
import socket
from sys import maxint

from sqlalchemy import (Column, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint,
                        Index)
from sqlalchemy.orm import (relation, contains_eager, column_property, backref,
                            deferred, defer, undefer, aliased, lazyload)
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import (Base, Service, Host, DnsRecord, DnsDomain,
                                Machine, Fqdn, Personality, Archetype)
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'service_instance'
_ABV = 'svc_inst'


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a host for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__ = _TN
    _class_label = 'Service Instance'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    service_id = Column(Integer, ForeignKey('service.id',
                                            name='%s_svc_fk' % _ABV),
                        nullable=False)
    name = Column(AqStr(64), nullable=False)
    max_clients = Column(Integer, nullable=True)  # null means 'no limit'
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    service = relation(Service, lazy=False, innerjoin=True, backref='instances')

    __table_args__ = (UniqueConstraint(service_id, name, name='svc_inst_uk'),)

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.service.name, self.name)
        return self.format_helper(format_spec, instance)

    @property
    def cfg_path(self):
        return 'service/%s/%s' % (self.service.name, self.name)

    @property
    def client_count(self):
        """Return the number of clients bound to this service.

        The calculation is tricky if cluster aligned services are involved.
        In that case, any clusters that are bound to the instance should count
        as though max_members are bound.  The tricky bit is de-duplication.

        """
        from aquilon.aqdb.model import Cluster, MetaCluster, MetaClusterMember

        session = object_session(self)

        # personalities by service
        q = session.query(Personality.id)
        q = q.join(Archetype).filter(Archetype.cluster_type != None)
        q = q.filter(Personality.services.contains(self.service))
        personality_ids = [p[0] for p in q]

        # personalities by archetype service
        q = session.query(Personality.id)
        q = q.join(Archetype).filter(Archetype.cluster_type != None)
        q = q.filter(Archetype.services.contains(self.service))
        personality_ids.extend([p[0] for p in q])

        if not personality_ids:
            # By far, the common case.
            return self._client_count

        clusters = {}

        # Meta
        McAlias = aliased(MetaCluster)
        q = session.query(Cluster.name, Cluster.max_hosts)
        # Force orm to look for mc - service relation
        q = q.join('_metacluster', (McAlias,
                        MetaClusterMember.metacluster_id == McAlias.id))
        q = q.filter(McAlias.service_bindings.contains(self))
        q = q.filter(McAlias.personality_id.in_(personality_ids))

        for name, max_host in q.all():
            clusters[name] = max_host

        # Esx et al.
        q = session.query(Cluster.name, Cluster.max_hosts)
        q = q.filter(Cluster.cluster_type != 'meta')
        q = q.filter(Cluster.service_bindings.contains(self))
        q = q.filter(Cluster.personality_id.in_(personality_ids))

        for name, max_host in q.all():
            clusters[name] = max_host

        adjusted_count = sum(clusters.itervalues())

        q = session.query(Host)
        q = q.filter(Host.services_used.contains(self))
        q = q.outerjoin('_cluster', 'cluster', from_joinpoint=True)
        q = q.filter(or_(Cluster.id == None,
                         ~Cluster.personality_id.in_(personality_ids)))
        adjusted_count += q.count()
        return adjusted_count

    @property
    def client_fqdns(self):
        session = object_session(self)
        q = session.query(DnsRecord)
        q = q.join(Machine, Host)
        q = q.filter(Host.services_used.contains(self))
        q = q.reset_joinpoint()
        # Due to aliases we have to explicitely tell how do we link to Fqdn
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id), DnsDomain)
        q = q.options(contains_eager('fqdn'))
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(DnsDomain.name, Fqdn.name)
        return [str(sys.fqdn) for sys in q.all()]

    @property
    def server_fqdns(self):
        from aquilon.aqdb.model import ServiceInstanceServer
        session = object_session(self)
        q = session.query(DnsRecord)
        q = q.join(Machine, Host, ServiceInstanceServer)
        q = q.filter_by(service_instance=self)
        q = q.reset_joinpoint()
        # Due to aliases we have to explicitely tell how do we link to Fqdn
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id), DnsDomain)
        q = q.options(contains_eager('fqdn'))
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(DnsDomain.name, Fqdn.name)
        return [str(sys.fqdn) for sys in q.all()]

    @property
    def server_ips(self):
        from aquilon.aqdb.model import ServiceInstanceServer
        session = object_session(self)
        q = session.query(DnsRecord)
        q = q.join(Machine, Host, ServiceInstanceServer)
        q = q.filter_by(service_instance=self)
        q = q.reset_joinpoint()
        # Due to aliases we have to explicitely tell how do we link to Fqdn
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id), DnsDomain)
        q = q.options(contains_eager('fqdn'))
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(DnsDomain.name, Fqdn.name)
        ips = []
        for dbdns_rec in q.all():
            if hasattr(dbdns_rec, 'ip'):
                ips.append(dbdns_rec.ip)
                continue
            try:
                ips.append(socket.gethostbyname(str(dbdns_rec.fqdn)))
            except socket.gaierror:  # pragma: no cover
                # For now this fails silently.  It may be correct to raise
                # an error here but the timing could be unpredictable.
                pass
        return ips

    @property
    def enforced_max_clients(self):
        if self.max_clients is not None:
            return self.max_clients
        return self.service.max_clients

    @classmethod
    def get_mapped_instance_cache(cls, dbpersonality, dblocation, dbservices,
                                  dbnetwork=None):
        """Returns dict of requested services to closest mapped instances."""
        # Can't import these on init as ServiceInstance is a dependency.
        # Could think about moving this method definition out to one of
        # these classes.
        from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap

        session = object_session(dblocation)

        location_ids = [loc.id for loc in dblocation.parents]
        location_ids.append(dblocation.id)
        location_ids.reverse()

        # Calculate the priority of services mapped to a given location. We'll
        # pick the instance mapped at the location of lowest priority
        loc_priorities = {}
        for idx, loc_id in enumerate(location_ids):
            loc_priorities[loc_id] = idx

        # Prefer network-based maps over location-based maps
        loc_priorities[None] = -1

        # Use maxint as priority to mark empty slots
        instance_cache = {}
        instance_priority = defaultdict(lambda: maxint)

        search_maps = []
        if dbpersonality:
            search_maps.append(PersonalityServiceMap)
        search_maps.append(ServiceMap)
        for map_type in search_maps:
            # search only for missing ids
            missing_ids = [dbservice.id for dbservice in dbservices
                           if dbservice not in instance_cache]

            # An empty "WHERE ... IN (...)" clause might be expensive to
            # evaluate even if it returns nothing, so avoid doing that.
            if not missing_ids:
                continue

            ## get map by locations
            q = session.query(map_type.location_id, ServiceInstance)
            q = q.filter(map_type.service_instance_id == ServiceInstance.id)
            if map_type == PersonalityServiceMap:
                q = q.filter_by(personality=dbpersonality)
            q = q.filter(ServiceInstance.service_id.in_(missing_ids))
            q = q.options(defer(ServiceInstance.comments),
                          undefer(ServiceInstance._client_count),
                          lazyload(ServiceInstance.service))

            if dbnetwork:
                q = q.filter(or_(map_type.location_id.in_(location_ids),
                                 map_type.network_id == dbnetwork.id))
            else:
                q = q.filter(map_type.location_id.in_(location_ids))

            for location_id, si in q:
                priority = loc_priorities[location_id]
                service = si.service

                if instance_priority[service] > priority:
                    instance_cache[service] = [si]
                    instance_priority[service] = priority
                elif instance_priority[service] == priority:
                    instance_cache[service].append(si)

        return instance_cache

service_instance = ServiceInstance.__table__  # pylint: disable=C0103
service_instance.info['abrev'] = _ABV
service_instance.info['unique_fields'] = ['name', 'service']


class BuildItem(Base):
    """ Identifies the service_instance bindings of a machine. """
    __tablename__ = 'build_item'

    host_id = Column('host_id', Integer, ForeignKey('host.machine_id',
                                                    ondelete='CASCADE',
                                                    name='build_item_host_fk'),
                     nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 nullable=False)

    __table_args__ = (PrimaryKeyConstraint(host_id, service_instance_id),
                      Index('build_item_si_idx', service_instance_id))

ServiceInstance.clients = relation(Host, secondary=BuildItem.__table__,
                                   backref=backref("services_used",
                                                   cascade="all"))

# Make this a column property so it can be undeferred on bulk loads
ServiceInstance._client_count = column_property(
    select([func.count()],
            BuildItem.service_instance_id == ServiceInstance.id)
    .label("_client_count"), deferred=True)
