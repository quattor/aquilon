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
                            lazyload, object_session)
from sqlalchemy.sql import or_

from aquilon.aqdb.model import (Base, Location, ServiceInstance, Network,
                                Personality)

_TN = 'service_map'


class ServiceMap(Base):
    """ Service Map: mapping a service_instance to a location.
        The rows in this table assert that an instance is a valid useable
        default that clients can choose as their provider during service
        autoconfiguration. """

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
    def mapped_to(self):
        if self.location:
            mapped_to = self.location
        else:
            mapped_to = self.network

        return mapped_to

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
        location_ids.reverse()

        # Calculate the priority of services mapped to a given location. We'll
        # pick the instance mapped at the location of lowest priority
        loc_priorities = {}
        for idx, loc_id in enumerate(location_ids):
            loc_priorities[loc_id] = idx

        # Prefer network-based maps over location-based maps
        loc_priorities[None] = -1

        # Use maxsize as priority to mark empty slots
        instance_cache = {}
        instance_priority = defaultdict(lambda: maxsize)

        queries = []

        if dbpersonality:
            q = session.query(ServiceMap.location_id, ServiceInstance)
            q = q.filter(ServiceMap.personality == dbpersonality)
            queries.append(q)

        q = session.query(ServiceMap.location_id, ServiceInstance)
        q = q.filter(ServiceMap.personality == None)
        queries.append(q)

        for q in queries:
            # search only for missing ids
            missing_ids = [dbservice.id for dbservice in dbservices
                           if dbservice not in instance_cache]

            # An empty "WHERE ... IN (...)" clause might be expensive to
            # evaluate even if it returns nothing, so avoid doing that.
            if not missing_ids:
                continue

            # get map by locations
            q = q.filter(ServiceMap.service_instance_id == ServiceInstance.id)
            q = q.filter(ServiceInstance.service_id.in_(missing_ids))
            q = q.options(defer(ServiceInstance.comments),
                          undefer(ServiceInstance._client_count),
                          lazyload(ServiceInstance.service))

            if dbnetwork:
                q = q.filter(or_(ServiceMap.location_id.in_(location_ids),
                                 ServiceMap.network_id == dbnetwork.id))
            else:
                q = q.filter(ServiceMap.location_id.in_(location_ids))

            for location_id, si in q:
                priority = loc_priorities[location_id]
                service = si.service

                if instance_priority[service] > priority:
                    instance_cache[service] = [si]
                    instance_priority[service] = priority
                elif instance_priority[service] == priority:
                    instance_cache[service].append(si)

        return instance_cache
