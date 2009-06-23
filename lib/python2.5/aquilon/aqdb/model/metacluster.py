# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""
    A metacluster is a grouping of two or more clusters grouped together for
    wide-area failover scenarios (So far only for vmware based clusters)
"""

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence,
                        ForeignKey, UniqueConstraint)

from sqlalchemy.orm import relation, backref
from sqlalchemy.ext.associationproxy import association_proxy

from aquilon.aqdb.model import Base, Cluster
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
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments      = Column(String(255))

    members = association_proxy('clusters', 'cluster',
                                creator=_metacluster_member_by_cluster)

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
            if len(mc.members) == mc.max_clusters:
                msg = '%s already at maximum capacity (%s)'% (mc.name,
                                                              mc.max_clusters)
                raise ValueError(msg)
        super(MetaClusterMember, self).__init__(**kw)

metamember = MetaClusterMember.__table__
metamember.primary_key.name = '%s_pk'% (_MCM)
metamember.append_constraint(
    UniqueConstraint('cluster_id', name='%s_uk'% (_MCM)))
