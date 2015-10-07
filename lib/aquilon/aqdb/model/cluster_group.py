# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.model import Base, Cluster

_CG = "cluster_group"
_CGM = "cluster_group_member"


class ClusterGroup(Base):
    __tablename__ = _CG

    id = Column(Integer, Sequence("%s_id_seq" % _CG), primary_key=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))


class __ClusterGroupMember(Base):
    __tablename__ = _CGM

    cluster_group_id = Column(ForeignKey(ClusterGroup.id, ondelete='CASCADE'),
                              nullable=False)

    cluster_id = Column(ForeignKey(Cluster.id, ondelete='CASCADE'),
                        nullable=False, unique=True)

    __table_args__ = (PrimaryKeyConstraint(cluster_group_id, cluster_id),)

ClusterGroup.members = relation(Cluster,
                                secondary=__ClusterGroupMember.__table__,
                                passive_deletes=True,
                                backref=backref('cluster_group', uselist=False,
                                                passive_deletes=True))
