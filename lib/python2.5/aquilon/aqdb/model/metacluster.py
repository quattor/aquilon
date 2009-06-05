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

from aquilon.aqdb.model import Base, Host, Network, Cluster
from aquilon.aqdb.column_types.aqstr import AqStr

_MCT = 'metacluster'
class MetaCluster(Base):
    """
        A metacluster is a grouping of two or more clusters grouped together for
        wide-area failover scenarios (So far only for vmware based clusters)
    """

    __tablename__ = _MCT

    id = Column(Integer, Sequence('%s_seq'%(_MCT)), primary_key=True)
    name = Column(AqStr(64), nullable=False)
    #TODO: is this always to be nullable?
    network_id = Column(Integer, ForeignKey('network.id',
                                            name='%s_network_fk'%(_MCT)),
                        nullable=True)
    max_members = Column(Integer, default=2, nullable=False)
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments      = Column(String(255))

    members = association_proxy('metacluster', 'cluster')
    #TODO: append function that checks if current members+1 >= max_members

metacluster=MetaCluster.__table__
metacluster.primary_key.name='%s_pk'%(_MCT)
metacluster.append_constraint(UniqueConstraint('name', name='%s_uk'%(_MCT)))


_MCM = 'metacluster_member'
class MetaClusterMember(Base):
    __tablename__ = _MCM

    metacluster_id = Column(Integer, ForeignKey('metacluster.id',
                                                name='%s_meta_fk'%(_MCM),
                                                ondelete='CASCADE'),
                            primary_key=True)

    cluster_id = Column(Integer, ForeignKey('clstr.id',
                                            name='%s_clstr_fk'%(_MCM),
                                            ondelete='CASCADE'),
                        primary_key=True)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    metacluster = relation(MetaCluster, lazy=False, uselist=False,
                            backref=backref('metacluster', cascade='all, delete-orphan'))

    cluster = relation(Cluster, lazy=False, cascade='all',
                       backref=backref('mc_cluster', cascade='all, delete-orphan'))

    def __init__(self, **kw):
        mc = kw['metacluster']
        if len(mc.members) == mc.max_members:
            msg = '%s already at maximum capacity (%s)'%(mc.name, mc.max_members)
            raise ValueError(msg)
        super(MetaClusterMember, self).__init__(**kw)

metamember = MetaClusterMember.__table__
metamember.primary_key.name = '%s_pk'%(_MCM)
metamember.append_constraint(UniqueConstraint('cluster_id', name='%s_uk'))
