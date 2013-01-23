# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
""" see class.__doc__ for description """
from datetime import datetime
import socket

from sqlalchemy import (Column, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import (relation, contains_eager, column_property, backref,
                            deferred, undefer, aliased)
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import (Base, Service, Host, DnsRecord, DnsDomain,
                                Machine, Fqdn, Personality, Archetype)
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.column_types import Enum
from collections import defaultdict

_TN = 'service_instance'
_ABV = 'svc_inst'

# list of possible external service managers to enable federated control to
MANAGERS = ['aqd', 'resourcepool']


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
    manager = Column(Enum(32, MANAGERS), default='aqd', nullable=False)
    comments = Column(String(255), nullable=True)

    service = relation(Service, lazy=False, innerjoin=True, backref='instances')

    # _client_count is defined later in this file
    # nas_disk_count and nas_machine_count are defined in disk.py

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.service.name, self.name)
        return self.format_helper(format_spec, instance)

    def __lt__(self, other):
        return tuple([self.service.name,
                      self.name]) < tuple([other.service.name, other.name])

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
        from aquilon.aqdb.model import (ServiceMap, PersonalityServiceMap,
                                        Location, Network)
        session = object_session(dblocation)
        cache = {}

        ## all relevant locations
        location_ids = []
        location_ids.append(dblocation.id)
        for loc in reversed(dblocation.parents):
            location_ids.append(loc.id)

        search_maps = []
        if dbpersonality:
            search_maps.append(PersonalityServiceMap)
        search_maps.append(ServiceMap)
        for map_type in search_maps:
            # search only for missing ids
            missing_ids = []
            for dbservice in dbservices:
                if not cache.get(dbservice):
                    missing_ids.append(dbservice.id)

            ## get map by locations
            q = session.query(map_type)
            if map_type == PersonalityServiceMap:
                q = q.filter_by(personality=dbpersonality)
            q = q.join('service_instance').filter(
                ServiceInstance.service_id.in_(missing_ids))
            q = q.options(contains_eager('service_instance'),
                          undefer('service_instance._client_count'))

            if dbnetwork:
                q = q.reset_joinpoint()
                q = q.outerjoin('location')
                q = q.reset_joinpoint()
                q = q.outerjoin('network')
                q = q.filter(or_(Location.id.in_(location_ids),
                                 Network.id==dbnetwork.id))
            else:
                q = q.reset_joinpoint()
                q = q.join('location')
                q = q.filter(Location.id.in_(location_ids))

            # convert results in dict
            m_dict = defaultdict(list)
            n_dict = defaultdict(list)
            for service_map in q.all():
                if service_map.location_id:
                    key = (service_map.service.id, service_map.location.id)
                    m_dict[key].append(service_map.service_instance)
                else:
                    key = service_map.service.id
                    n_dict[key].append(service_map.service_instance)

            if not m_dict and not n_dict:
                continue

            # choose based on proximity
            for dbservice in dbservices:
                if dbservice.id in n_dict:
                    key = dbservice.id
                    cache[dbservice] = n_dict[key][:]
                else:
                    for lid in location_ids:
                        key = (dbservice.id, lid)
                        if key in m_dict:
                            cache[dbservice] = m_dict[key][:]
                            break

        return cache


service_instance = ServiceInstance.__table__  # pylint: disable=C0103

service_instance.primary_key.name = 'svc_inst_pk'
service_instance.append_constraint(
    UniqueConstraint('service_id', 'name', name='svc_inst_uk'))
service_instance.info['abrev'] = _ABV
service_instance.info['unique_fields'] = ['name', 'service']

class BuildItem(Base):
    """ Identifies the service_instance bindings of a machine. """
    __tablename__ = 'build_item'

    host_id = Column('host_id', Integer, ForeignKey('host.machine_id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                     primary_key=True)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 primary_key=True)


build_item = BuildItem.__table__  # pylint: disable=C0103
build_item.primary_key.name = 'build_item_pk'

ServiceInstance.clients = relation(Host, secondary=build_item,
                                   backref=backref("services_used",
                                                   cascade="all"))

# Make this a column property so it can be undeferred on bulk loads
ServiceInstance._client_count = column_property(
    select([func.count()],
            BuildItem.service_instance_id == ServiceInstance.id)
    .label("_client_count"), deferred=True)
