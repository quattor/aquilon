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

from sqlalchemy import (Column, Integer, DateTime, Boolean, ForeignKey,
                        UniqueConstraint, PrimaryKeyConstraint)

from sqlalchemy.orm import (relation, backref, deferred, validates,
                            object_session)
from sqlalchemy.orm.attributes import instance_state
from sqlalchemy.orm.interfaces import MapperExtension
from sqlalchemy.ext.associationproxy import association_proxy

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
    __mapper_args__ = {'polymorphic_identity': 'meta'}
    _class_label = "Metacluster"

    id = Column(Integer, ForeignKey(Cluster.id, name='meta_cluster_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    max_clusters = Column(Integer, nullable=False)

    high_availability = Column(Boolean(name="%s_ha_ck" % _MCT), default=False,
                               nullable=False)

    members = association_proxy('_clusters', 'cluster',
                                creator=lambda x: MetaClusterMember(cluster=x))

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
            cap = cluster.get_total_capacity()
            for name, value in cap.items():
                if name in building_capacity[building]:
                    building_capacity[building][name] += value
                else:
                    building_capacity[building][name] = value

        # Convert the per-building dict of resources to per-resource list of
        # building-provided values
        resmap = convert_resources(building_capacity.values())

        # high_availability is down_buildings_threshold == 1. So if high
        # availability is enabled, drop the largest value from every resource
        # list
        for name in resmap:
            reslist = sorted(resmap[name])
            if self.high_availability:
                reslist = reslist[:-1]
            resmap[name] = sum(reslist)

        return resmap

    def get_total_usage(self):
        usage = {}
        for cluster in self.members:
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
        if len(self.members) > self.max_clusters:
            raise ArgumentError("{0} has {1} clusters bound, which exceeds "
                                "the requested limit of {2}."
                                .format(self, len(self.members),
                                        self.max_clusters))

        if self.metacluster:
            raise ArgumentError("Metaclusters can't contain other "
                                "metaclusters.")

        # Small optimization: avoid enumerating all the clusters/VMs if high
        # availability is not enabled
        if self.high_availability:
            capacity = self.get_total_capacity()
            usage = self.get_total_usage()
            for name, value in usage.items():
                # Skip resources that are not restricted
                if name not in capacity:
                    continue
                if value > capacity[name]:
                    raise ArgumentError("{0} is over capacity regarding {1}: "
                                        "wanted {2}, but the limit is {3}."
                                        .format(self, name, value, capacity[name]))
        return

    @validates('_clusters')
    def validate_cluster_member(self, key, value):
        session = object_session(self)
        with session.no_autoflush:
            self.validate_membership(value.cluster)
        return value

    def validate_membership(self, cluster):
        if (cluster.branch != self.branch or
            cluster.sandbox_author != self.sandbox_author):
            raise ArgumentError("{0} {1} {2} does not match {3:l} {4} "
                                "{5}.".format(cluster,
                                              cluster.branch.branch_type,
                                              cluster.authored_branch,
                                              self,
                                              self.branch.branch_type,
                                              self.authored_branch))

metacluster = MetaCluster.__table__  # pylint: disable=C0103
metacluster.info['unique_fields'] = ['name']


class ValidateMetaCluster(MapperExtension):
    """ Helper class to perform validation on metacluster membership changes """

    def after_insert(self, mapper, connection, instance):
        """ Validate the metacluster after a new member has been added """
        instance.metacluster.validate()

    def after_delete(self, mapper, connection, instance):
        """ Validate the metacluster after a member has been deleted """
        # This is a little tricky. If the instance got deleted through an
        # association proxy, then instance.cluster will be None (although
        # instance.cluster_id still has the right value).
        if instance.metacluster:
            metacluster = instance.metacluster
        else:
            state = instance_state(instance)
            metacluster = state.committed_state['metacluster']
        metacluster.validate()


class MetaClusterMember(Base):
    """ Binds clusters to metaclusters """
    __tablename__ = _MCM

    metacluster_id = Column(Integer, ForeignKey(MetaCluster.id,
                                                name='%s_meta_fk' % _MCM,
                                                ondelete='CASCADE'),
                            nullable=False)

    cluster_id = Column(Integer, ForeignKey(Cluster.id,
                                            name='%s_clstr_fk' % _MCM,
                                            ondelete='CASCADE'),
                        nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    """
        Association Proxy and relation cascading:
        We need cascade=all on backrefs so that deletion propagates to avoid
        AssertionError: Dependency rule tried to blank-out primary key column on
        deletion of the Metacluster and it's links. On the contrary do not have
        cascade='all' on the forward mapper here, else deletion of metaclusters
        and their links also causes deleteion of clusters (BAD)
    """

    metacluster = relation(MetaCluster, lazy='subquery', innerjoin=True,
                           foreign_keys=metacluster_id,
                           backref=backref('_clusters',
                                           cascade='all, delete-orphan'))

    # This is a one-to-one relation, so we need uselist=False on the backref
    cluster = relation(Cluster, lazy='subquery', innerjoin=True,
                       foreign_keys=cluster_id,
                       backref=backref('_metacluster', uselist=False,
                                       cascade='all, delete-orphan'))

    __table_args__ = (PrimaryKeyConstraint(metacluster_id, cluster_id,
                                           name="%s_pk" % _MCM),
                      UniqueConstraint(cluster_id, name='%s_uk' % _MCM))
    __mapper_args__ = {'extension': ValidateMetaCluster()}

metamember = MetaClusterMember.__table__  # pylint: disable=C0103
metamember.info['unique_fields'] = ['metacluster', 'cluster']
