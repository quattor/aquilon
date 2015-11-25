# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
""" Maps service instances to locations. See class.__doc__ """

from collections import defaultdict
from datetime import datetime
from sys import maxsize

from sqlalchemy import (Column, Integer, Sequence, DateTime, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import (relation, deferred, backref, defer, undefer,
                            lazyload, contains_eager, object_session)
from sqlalchemy.sql import or_, null

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.model import (Base, Location, Desk, Rack, Room, Bunker,
                                Building, City, Campus, Country, Continent, Hub,
                                Company, ServiceInstance, Network, Personality)

_TN = 'service_map'

# TODO: We could calculate this map by building a graph of Location subclasses
# using Location.valid_parents as edges, and then doing a topological sort
# NOTE: The actual values here are unimportant, what matters is their order
_LOCATION_PRIORITY = {
    # Rack and Desk are at the same level
    Rack: 1000,
    Desk: 1000,
    Room: 1100,
    Bunker: 1200,
    Building: 1300,
    City: 1400,
    Campus: 1500,
    Country: 1600,
    Continent: 1700,
    Hub: 1800,
    Company: 1900,
}

# NOTE: The actual value here is unimportant, what matters is the order wrt.
# location-based priorities
_NETWORK_PRIORITY = 100

# NOTE: The actual values here are unimportant, only their order matters
_TARGET_PERSONALITY = 100
_TARGET_GLOBAL = 1000


class ServiceMap(Base):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration.

        The contained information is actually a triplet:
            - The service instance to use,
            - Rules for the scope where the map is valid,
            - Rules for which objects does the map apply.
    """

    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    service_instance_id = Column(ForeignKey(ServiceInstance.id,
                                            ondelete='CASCADE'),
                                 nullable=False)

    personality_id = Column(ForeignKey(Personality.id, ondelete='CASCADE'),
                            nullable=True, index=True)

    location_id = Column(ForeignKey(Location.id, ondelete='CASCADE'),
                         nullable=True, index=True)

    network_id = Column(ForeignKey(Network.id, ondelete='CASCADE'),
                        nullable=True, index=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    service_instance = relation(ServiceInstance, innerjoin=True,
                                backref=backref('service_map',
                                                cascade="all, delete-orphan",
                                                passive_deletes=True))
    personality = relation(Personality)
    location = relation(Location)
    network = relation(Network)

    __table_args__ = (UniqueConstraint(service_instance_id, personality_id,
                                       location_id, network_id,
                                       name='%s_uk' % _TN),)

    @property
    def service(self):
        return self.service_instance.service

    @property
    def scope_priority(self):
        if self.network:
            return _NETWORK_PRIORITY
        else:
            try:
                return _LOCATION_PRIORITY[type(self.location)]
            except KeyError:  # pragma: no cover
                raise InternalError("The service map is not prepared to handle "
                                    "location class %r" % type(self.location))

    @property
    def object_priority(self):
        if self.personality:
            return _TARGET_PERSONALITY
        else:
            return _TARGET_GLOBAL

    @property
    def priority(self):
        return (self.object_priority, self.scope_priority)

    @property
    def scope(self):
        if self.location:
            return self.location
        else:
            return self.network

    def __init__(self, network=None, location=None, **kwargs):
        super(ServiceMap, self).__init__(network=network, location=location,
                                         **kwargs)
        if network and location:  # pragma: no cover
            raise ValueError("A service can't be mapped to a Network and a "
                             "Location at the same time")

        if network is None and location is None:  # pragma: no cover
            raise ValueError("A service should by mapped to a Network or a "
                             "Location")

    @staticmethod
    def get_mapped_instance_cache(dbservices, dbpersonality, dblocation,
                                  dbnetwork=None):
        """Returns dict of requested services to closest mapped instances."""

        session = object_session(dblocation)

        location_ids = [loc.id for loc in dblocation.parents]
        location_ids.append(dblocation.id)

        q = session.query(ServiceMap)

        # Rules for filtering by target object
        if dbpersonality:
            q = q.filter(or_(ServiceMap.personality_id == null(),
                             ServiceMap.personality_id == dbpersonality.id))
        else:
            q = q.filter_by(personality=None)

        # Rules for filtering by location/scope
        if dbnetwork:
            q = q.filter(or_(ServiceMap.location_id.in_(location_ids),
                             ServiceMap.network_id == dbnetwork.id))
        else:
            q = q.filter(ServiceMap.location_id.in_(location_ids))

        q = q.join(ServiceInstance)
        q = q.filter(ServiceInstance.service_id.in_(srv.id for srv in dbservices))
        q = q.options(contains_eager('service_instance'),
                      defer('service_instance.comments'),
                      undefer('service_instance._client_count'),
                      lazyload('service_instance.service'))

        instance_cache = {}
        instance_priority = defaultdict(lambda: (maxsize,))

        # For every service, we want the instance(s) with the lowest priority
        for map in q:
            si = map.service_instance
            service = si.service

            if instance_priority[service] > map.priority:
                instance_cache[service] = [si]
                instance_priority[service] = map.priority
            elif instance_priority[service] == map.priority:
                instance_cache[service].append(si)

        return instance_cache
