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
""" see class.__doc__ for description """

from datetime import datetime
from six import itervalues

from sqlalchemy import (Column, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint, PrimaryKeyConstraint)
from sqlalchemy.orm import (relation, contains_eager, column_property, backref,
                            deferred, aliased, object_session)
from sqlalchemy.sql import select, func, or_, null

from aquilon.aqdb.model import (Base, Service, Host, DnsRecord, DnsDomain,
                                HardwareEntity, Fqdn)
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = 'service_instance'


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a host for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__ = _TN
    _class_label = 'Service Instance'

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)
    service_id = Column(ForeignKey(Service.id), nullable=False)
    name = Column(AqStr(64), nullable=False)
    max_clients = Column(Integer, nullable=True)  # null means 'no limit'
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = Column(String(255), nullable=True)

    service = relation(Service, lazy=False, innerjoin=True, backref='instances')

    __table_args__ = (UniqueConstraint(service_id, name),
                      {'info': {'unique_fields': ['name', 'service']}},)

    def __init__(self, name=None, **kwargs):
        name = AqStr.normalize(name)
        super(ServiceInstance, self).__init__(name=name, **kwargs)

    @property
    def qualified_name(self):
        return self.service.name + "/" + self.name

    @property
    def client_count(self):
        """Return the number of clients bound to this service.

        The calculation is tricky if cluster aligned services are involved.
        In that case, any clusters that are bound to the instance should count
        as though max_members are bound.  The tricky bit is de-duplication.

        """
        from aquilon.aqdb.model import Cluster, MetaCluster

        # Check if the service instance is used by any cluster-bound personality
        persst_ids = self.service.cluster_aligned_personalities
        if not persst_ids:
            # By far, the common case.
            return self._client_count

        session = object_session(self)

        # Meta
        McAlias = aliased(MetaCluster)
        q = session.query(Cluster.name, Cluster.max_hosts)
        # Force orm to look for mc - service relation
        q = q.join(McAlias, Cluster.metacluster)
        q = q.filter(McAlias.services_used.contains(self))
        q = q.filter(McAlias.personality_stage_id.in_(persst_ids))

        clusters = {name: max_host for name, max_host in q}

        # Esx et al.
        q = session.query(Cluster.name, Cluster.max_hosts)
        q = q.filter(Cluster.cluster_type != 'meta')
        q = q.filter(Cluster.services_used.contains(self))
        q = q.filter(Cluster.personality_stage_id.in_(persst_ids))

        for name, max_host in q:
            clusters[name] = max_host

        adjusted_count = sum(itervalues(clusters))

        q = session.query(Host)
        q = q.filter(Host.services_used.contains(self))
        q = q.outerjoin('_cluster', 'cluster')
        q = q.filter(or_(Cluster.id == null(),
                         ~Cluster.personality_stage_id.in_(persst_ids)))
        adjusted_count += q.count()
        return adjusted_count

    @property
    def client_fqdns(self):
        session = object_session(self)
        q = session.query(DnsRecord)
        q = q.join(HardwareEntity, Host)
        q = q.filter(Host.services_used.contains(self))
        q = q.reset_joinpoint()
        # Due to aliases we have to explicitely tell how do we link to Fqdn
        q = q.join((Fqdn, DnsRecord.fqdn_id == Fqdn.id), DnsDomain)
        q = q.options(contains_eager('fqdn'))
        q = q.options(contains_eager('fqdn.dns_domain'))
        q = q.order_by(DnsDomain.name, Fqdn.name)
        return [str(sys.fqdn) for sys in q]

    @property
    def cluster_names(self):
        """Returns all clusters involved, including metaclusters."""
        from aquilon.aqdb.model import Cluster
        session = object_session(self)
        q = session.query(Cluster.name)
        q = q.filter(Cluster.services_used.contains(self))
        return [name for record in q for name in record]

    @property
    def enforced_max_clients(self):
        if self.max_clients is not None:
            return self.max_clients
        return self.service.max_clients


class __BuildItem(Base):
    """ Identifies the service_instance bindings of a machine. """
    __tablename__ = 'build_item'

    host_id = Column(ForeignKey(Host.hardware_entity_id, ondelete='CASCADE'),
                     nullable=False)

    service_instance_id = Column(ForeignKey(ServiceInstance.id),
                                 nullable=False, index=True)

    __table_args__ = (PrimaryKeyConstraint(host_id, service_instance_id),)

ServiceInstance.clients = relation(Host, secondary=__BuildItem.__table__,
                                   backref=backref("services_used",
                                                   cascade="all",
                                                   passive_deletes=True))

# Make this a column property so it can be undeferred on bulk loads
ServiceInstance._client_count = column_property(
    select([func.count()],
           __BuildItem.service_instance_id == ServiceInstance.id)
    .label("_client_count"), deferred=True)
