# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2013  Contributor
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

from sqlalchemy import (Column, Integer, String, DateTime, Sequence,
                        ForeignKey, UniqueConstraint)

from sqlalchemy.orm import relation, backref
from sqlalchemy.orm.session import object_session
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.model import Base, Cluster, ServiceInstance
from aquilon.aqdb.column_types.aqstr import AqStr

def _metacluster_member_by_cluster(cl):
    """ creator function for metacluster members """
    return MetaClusterMember(cluster=cl)

_MCT = 'metacluster'
class MetaCluster(Base):
    """
        A metacluster is a grouping of two or more clusters grouped together for
        wide-area failover scenarios (So far only for vmware based clusters).
        Network is nullable for metaclusters that do not utilize IP failover.
    """

    __tablename__ = _MCT

    id = Column(Integer, Sequence('%s_seq'%(_MCT)), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    max_clusters = Column(Integer, default=2, nullable=False)
    max_shares = Column(Integer, nullable=False)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255))

    members = association_proxy('clusters', 'cluster',
                                creator=_metacluster_member_by_cluster)

    @property
    def shares(self):
        q = object_session(self).query(ServiceInstance)
        q = q.join(['nas_disks', 'machine', '_cluster', 'cluster',
                    '_metacluster'])
        q = q.filter_by(metacluster=self)
        return q.all()

metacluster = MetaCluster.__table__
metacluster.primary_key.name = '%s_pk'% (_MCT)
metacluster.append_constraint(UniqueConstraint('name', name='%s_uk'% (_MCT)))


_MCM = 'metacluster_member'
class MetaClusterMember(Base):
    """ Binds clusters to metaclusters """
    __tablename__ = _MCM

    metacluster_id = Column(Integer, ForeignKey('metacluster.id',
                                                name='%s_meta_fk'% (_MCM),
                                                ondelete='CASCADE'),
                            #if a metacluser is delete so is the association
                            primary_key=True)

    cluster_id = Column(Integer, ForeignKey('clstr.id',
                                            name='%s_clstr_fk'% (_MCM),
                                            ondelete='CASCADE'),
                        #if a cluster is deleted, so is the association
                        primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    """
        Association Proxy and relation cascading:
        We need cascade=all on backrefs so that deletion propagates to avoid
        AssertionError: Dependency rule tried to blank-out primary key column on
        deletion of the Metacluster and it's links. On the contrary do not have
        cascade='all' on the forward mapper here, else deletion of metaclusters
        and their links also causes deleteion of clusters (BAD)
    """

    metacluster = relation(MetaCluster, lazy=False, uselist=False,
                            backref=backref('clusters', cascade='all'))

    cluster = relation(Cluster, lazy=False,
                       backref=backref('_metacluster', uselist=False,
                                       cascade='all'))

    def __init__(self, **kw):
        if kw.has_key('metacluster'):
            #when we append to the association proxy, there's no metacluster arg
            #which prevents this from being checked.
            mc = kw['metacluster']
            if len(mc.members) >= mc.max_clusters:
                msg = '%s already at maximum capacity (%s)'% (mc.name,
                                                              mc.max_clusters)
                raise ValueError(msg)
        super(MetaClusterMember, self).__init__(**kw)

metamember = MetaClusterMember.__table__
metamember.primary_key.name = '%s_pk'% (_MCM)
metamember.append_constraint(
    UniqueConstraint('cluster_id', name='%s_uk'% (_MCM)))
