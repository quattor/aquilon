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
""" see class.__doc__ for description """

from datetime import datetime
import socket

from sqlalchemy import (Column, Integer, Sequence, String, DateTime,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, contains_eager, column_property, backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.sql.expression import or_
from sqlalchemy.sql import select, func

from aquilon.aqdb.model import (Base, Service, Host, System, DnsDomain, Machine,
                                PrimaryNameAssociation)
from aquilon.aqdb.column_types.aqstr import AqStr

_TN  = 'service_instance'
_ABV = 'svc_inst'


class ServiceInstance(Base):
    """ Service instance captures the data around assignment of a host for a
        particular purpose (aka usage). If machines have a 'personality'
        dictated by the application they run """

    __tablename__  = _TN
    _class_label = 'Service Instance'

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    service_id = Column(Integer, ForeignKey('service.id',
                                            name='%s_svc_fk'%(_ABV)),
                        nullable=False)

    name = Column(AqStr(64), nullable=False)
    max_clients = Column(Integer, nullable=True) #null means 'no limit'
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    service = relation(Service, lazy=False, uselist=False, backref='instances')

    # _client_count is defined later in this file
    # nas_disk_count and nas_machine_count are defined in disk.py

    def __format__(self, format_spec):
        instance = "%s/%s" % (self.service.name, self.name)
        return self.format_helper(format_spec, instance)

    @property
    def cfg_path(self):
        return 'service/%s/%s'% (self.service.name, self.name)

    @property
    def client_count(self):
        """Return the number of clients bound to this service.

        The calculation is tricky if cluster aligned services are involved.
        In that case, any clusters that are bound to the instance should count
        as though max_members are bound.  The tricky bit is de-duplication.

        """
        from aquilon.aqdb.model import (ClusterServiceBinding, BuildItem,
                                        Cluster)
        session = object_session(self)

        cluster_types = self.service.aligned_cluster_types
        if not cluster_types:
            # By far, the common case.
            return self._client_count

        q = session.query(func.sum(Cluster.max_hosts))
        q = q.filter(Cluster.cluster_type.in_(cluster_types))
        q = q.join(ClusterServiceBinding)
        q = q.filter_by(service_instance=self)
        # Make sure it's a number
        adjusted_count = q.scalar() or 0

        q = session.query(BuildItem)
        q = q.filter_by(service_instance=self)
        q = q.outerjoin('host', '_cluster', 'cluster')
        q = q.filter(or_(Cluster.id==None,
                         ~Cluster.cluster_type.in_(cluster_types)))
        adjusted_count += q.count()
        return adjusted_count

    @property
    def client_fqdns(self):
        session = object_session(self)
        q = session.query(System)
        q = q.join(PrimaryNameAssociation, Machine, Host, BuildItem)
        q = q.filter_by(service_instance=self)
        q = q.reset_joinpoint()
        q = q.join(DnsDomain)
        q = q.options(contains_eager(System.dns_domain))
        q = q.order_by(DnsDomain.name, System.name)
        return [sys.fqdn for sys in q.all()]

    @property
    def server_fqdns(self):
        from aquilon.aqdb.model import ServiceInstanceServer
        session = object_session(self)
        q = session.query(System)
        q = q.join(PrimaryNameAssociation, Machine, Host, ServiceInstanceServer)
        q = q.filter_by(service_instance=self)
        q = q.reset_joinpoint()
        q = q.outerjoin(System.dns_domain)
        q = q.options(contains_eager(System.dns_domain))
        q = q.order_by(DnsDomain.name, System.name)
        return [sys.fqdn for sys in q.all()]

    @property
    def server_ips(self):
        from aquilon.aqdb.model import ServiceInstanceServer
        session = object_session(self)
        q = session.query(System)
        q = q.join(PrimaryNameAssociation, Machine, Host, ServiceInstanceServer)
        q = q.filter_by(service_instance=self)
        q = q.reset_joinpoint()
        q = q.outerjoin(System.dns_domain)
        q = q.options(contains_eager(System.dns_domain))
        q = q.order_by(DnsDomain.name, System.name)
        ips = []
        for system in q.all():
            if system.ip:
                ips.append(system.ip)
                continue
            try:
                ips.append(socket.gethostbyname(system.fqdn))
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
    def get_mapped_instance_cache(cls, dbpersonality, dblocation, dbservices):
        """Returns dict of requested services to closest mapped instances."""
        session = object_session(dbpersonality)
        if session.connection().dialect.name == 'oracle':
            return cls._oracle_get_mapped_instance_cache(dbpersonality,
                                                         dblocation,
                                                         dbservices)
        return cls._universal_get_mapped_instance_cache(dbpersonality,
                                                        dblocation, dbservices)

    @classmethod
    def _oracle_get_mapped_instance_cache(cls, dbpersonality, dblocation,
                                          dbservices):
        session = object_session(dbpersonality)

        q = session.query(ServiceInstance)
        # The in_ method does not work for relations in sqlalchemy 0.5.
        service_ids = [dbservice.id for dbservice in dbservices]
        q = q.filter(ServiceInstance.service_id.in_(service_ids))
        q = q.filter(ORACLE_PERSONALITY_SERVICE_MAP_EXISTS)
        q = q.params(location_id=dblocation.id,
                     personality_id=dbpersonality.id)

        cache = {}
        for dbsi in q.all():
            if not cache.get(dbsi.service):
                cache[dbsi.service] = []
            cache[dbsi.service].append(dbsi)

        missing_ids = []
        for dbservice in dbservices:
            if not cache.get(dbservice):
                missing_ids.append(dbservice.id)

        if not missing_ids:
            return cache

        q = session.query(ServiceInstance)
        q = q.filter(ServiceInstance.service_id.in_(missing_ids))
        q = q.filter(ORACLE_SERVICE_MAP_EXISTS)
        q = q.params(location_id=dblocation.id)
        for dbsi in q.all():
            if not cache.get(dbsi.service):
                cache[dbsi.service] = []
            cache[dbsi.service].append(dbsi)

        return cache

    @classmethod
    def _universal_get_mapped_instance_cache(cls, dbpersonality, dblocation,
                                             dbservices):
        # Can't import these on init as ServiceInstance is a dependency.
        # Could think about moving this method definition out to one of
        # these classes.
        from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap
        session = object_session(dbpersonality)
        cache = {}
        for dbservice in dbservices:
            for map_type in [PersonalityServiceMap, ServiceMap]:
                current_location = dblocation
                last_location = None
                while(not cache.get(dbservice) and
                      current_location is not None and
                      current_location != last_location):
                    q = session.query(map_type)
                    if map_type == PersonalityServiceMap:
                        q = q.filter_by(personality=dbpersonality)
                    q = q.filter_by(location=current_location)
                    q = q.join('service_instance').filter_by(service=dbservice)
                    cache[dbservice] = [map.service_instance
                                            for map in q.all()]
                    last_location = current_location
                    current_location = current_location.parent
        return cache


service_instance = ServiceInstance.__table__

service_instance.primary_key.name = 'svc_inst_pk'
service_instance.append_constraint(
    UniqueConstraint('service_id', 'name', name='svc_inst_uk'))
service_instance.info['abrev'] = _ABV
service_instance.info['unique_fields'] = ['name', 'service']

# This highly optimized filter is used to implement the logic in
# ServiceInstance._universal_get_archetype_map().
#
# It is best read inside-out starting at the deepest nesting.
# The numbers in the table aliases represent nesting level.
# The innermost (#4) select determines the hierarchy level for the locations
# of any service map entries for the given service instance.
# Layer #3 picks out the level of the most granular location available.
# Layer #2 gets the id for that location.
# The outermost layer selects all service instances for all archetype
# required services that are in the service map.  It filters on the
# location information to only pull the closest entries.
#
# Of note is that it assumes the standard table name of service_instance
# from the main query.  (It's the unaliased reference in the first AND
# clause.)
#
# This was duplicated for personality_service_map below.
ORACLE_SERVICE_MAP_EXISTS = """EXISTS (
SELECT 1
FROM service_instance si1, location l1, service_map sm1, service s1
WHERE si1.service_id = s1.id
AND service_instance.id = si1.id
AND s1.id IS NOT NULL
AND sm1.service_instance_id = si1.id
AND sm1.location_id = l1.id
AND l1.id in (
    SELECT l2.id FROM location l2
    WHERE LEVEL = (
        SELECT MIN(LEVEL) FROM location l3
        WHERE EXISTS (
            SELECT 1 FROM service_map sm4, service_instance si4
            WHERE sm4.location_id = l3.id
            AND sm4.service_instance_id = si4.id
            AND si4.service_id = s1.id
        )
        CONNECT BY l3.id = PRIOR l3.parent_id START WITH l3.id = :location_id
    )
    CONNECT BY l2.id = PRIOR l2.parent_id START WITH l2.id = :location_id
)
)"""

# See comments for ORACLE_SERVICE_MAP_EXISTS
# This is the same except personality_service_map is used instead of
# service_map, which requires personality_id as an additional parameter.
ORACLE_PERSONALITY_SERVICE_MAP_EXISTS = """EXISTS (
SELECT 1
FROM service_instance si1, location l1, personality_service_map sm1, service s1
WHERE si1.service_id = s1.id
AND service_instance.id = si1.id
AND s1.id IS NOT NULL
AND sm1.service_instance_id = si1.id
AND sm1.location_id = l1.id
AND sm1.personality_id = :personality_id
AND l1.id in (
    SELECT l2.id FROM location l2
    WHERE LEVEL = (
        SELECT MIN(LEVEL) FROM location l3
        WHERE EXISTS (
            SELECT 1 FROM personality_service_map sm4, service_instance si4
            WHERE sm4.location_id = l3.id
            AND sm4.service_instance_id = si4.id
            AND si4.service_id = s1.id
            AND sm4.personality_id = :personality_id
        )
        CONNECT BY l3.id = PRIOR l3.parent_id START WITH l3.id = :location_id
    )
    CONNECT BY l2.id = PRIOR l2.parent_id START WITH l2.id = :location_id
)
)"""


class BuildItem(Base):
    """ Identifies the service_instance bindings of a machine. """
    __tablename__ = 'build_item'

    #FIXME: remove id column. PK is machine/svc_inst
    id = Column(Integer, Sequence('build_item_id_seq'), primary_key=True)

    host_id = Column('host_id', Integer, ForeignKey('host.machine_id',
                                                     ondelete='CASCADE',
                                                     name='build_item_host_fk'),
                     nullable=False)

    service_instance_id = Column(Integer,
                                 ForeignKey('service_instance.id',
                                            name='build_item_svc_inst_fk'),
                                 nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    service_instance = relation(ServiceInstance, uselist=False,
                                backref=backref('clients'))

    host = relation(Host, uselist=False,
                    backref=backref('services_used',
                                    cascade="all, delete-orphan"))

    @property
    def cfg_path(self):
        return self.service_instance.cfg_path


build_item = BuildItem.__table__  # pylint: disable-msg=C0103, E1101

build_item.primary_key.name = 'build_item_pk'

build_item.append_constraint(
    UniqueConstraint('host_id', 'service_instance_id', name='build_item_uk'))

# Make this a column property so it can be undeferred on bulk loads
ServiceInstance._client_count = column_property(
    select([func.count()],
            BuildItem.service_instance_id == ServiceInstance.id)
    .label("_client_count"), deferred=True)
