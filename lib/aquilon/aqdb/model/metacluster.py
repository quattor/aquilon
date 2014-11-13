# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""
    A metacluster is a grouping of two or more clusters grouped together for
    wide-area failover scenarios (So far only for vmware based clusters)
"""

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import (relation, backref, deferred, validates,
                            object_session)

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base, Cluster
from aquilon.aqdb.model.cluster import convert_resources

_MCT = 'metacluster'
_MCM = 'metacluster_member'


class MetaCluster(Cluster):
    """
        A metacluster is a grouping of two or more clusters grouped
        together for wide-area failover scenarios (So far only for
        vmware based clusters).  Network is nullable for metaclusters
        that do not utilize IP failover.
    """

    __tablename__ = _MCT
    _class_label = "Metacluster"

    id = Column(ForeignKey(Cluster.id, ondelete='CASCADE'), primary_key=True)

    max_clusters = Column(Integer, nullable=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)
    __mapper_args__ = {'polymorphic_identity': 'meta'}

    # see cluster.minimum_location
    @property
    def minimum_location(self):
        location = None
        for cluster in self.members:
            if location:
                location = location.merge(cluster.location_constraint)
            else:
                location = cluster.location_constraint
        return location

    def get_total_capacity(self):
        # Key: building; value: list of cluster capacities inside that building
        building_capacity = {}
        for cluster in self.members:
            building = cluster.location_constraint.building
            if building not in building_capacity:
                building_capacity[building] = {}

            if not hasattr(cluster, 'get_total_capacity'):
                continue

            cap = cluster.get_total_capacity()
            for name, value in cap.items():
                if name in building_capacity[building]:
                    building_capacity[building][name] += value
                else:
                    building_capacity[building][name] = value

        # Convert the per-building dict of resources to per-resource list of
        # building-provided values
        resmap = convert_resources(building_capacity.values())

        for name in resmap:
            reslist = sorted(resmap[name])
            resmap[name] = sum(reslist)

        return resmap

    def get_total_usage(self):
        usage = {}
        for cluster in self.members:
            if not hasattr(cluster, 'get_total_usage'):
                continue

            for name, value in cluster.get_total_usage().items():
                if name in usage:
                    usage[name] += value
                else:
                    usage[name] = value
        return usage

    def all_objects(self):
        yield self
        for dbcls in self.members:
            for dbobj in dbcls.all_objects():
                yield dbobj

    def validate(self):
        """ Validate metacluster constraints """
        if self.max_clusters is not None and len(self.members) > self.max_clusters:
            raise ArgumentError("{0} has {1} clusters bound, which exceeds "
                                "the requested limit of {2}."
                                .format(self, len(self.members),
                                        self.max_clusters))

        if self.metacluster:  # pragma: no cover
            raise ArgumentError("Metaclusters can't contain other "
                                "metaclusters.")
        return

    @validates('members')
    def validate_cluster_member(self, key, value):  # pylint: disable=W0613
        session = object_session(self)
        with session.no_autoflush:
            self.validate_membership(value)
        return value

    def validate_membership(self, cluster):
        if self.allowed_personalities and \
                cluster.personality not in self.allowed_personalities:
            allowed = sorted("%s/%s" % (pers.archetype, pers.name)
                             for pers in self.allowed_personalities)
            raise ArgumentError("{0} is not allowed by the metacluster.  "
                                "Allowed personalities are: {1!s}"
                                .format(cluster.personality, ", ".join(allowed)))

        if cluster.branch != self.branch or \
           cluster.sandbox_author != self.sandbox_author:
            raise ArgumentError("{0} {1} {2} does not match {3:l} {4} "
                                "{5}.".format(cluster,
                                              cluster.branch.branch_type,
                                              cluster.authored_branch,
                                              self,
                                              self.branch.branch_type,
                                              self.authored_branch))


class __MetaClusterMember(Base):
    """ Binds clusters to metaclusters """
    __tablename__ = _MCM

    metacluster_id = Column(ForeignKey(MetaCluster.id, ondelete='CASCADE'),
                            nullable=False)

    cluster_id = Column(ForeignKey(Cluster.id, ondelete='CASCADE'),
                        nullable=False, unique=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (PrimaryKeyConstraint(metacluster_id, cluster_id),)

MetaCluster.members = relation(Cluster,
                               secondary=__MetaClusterMember.__table__,
                               backref=backref('metacluster', uselist=False))
