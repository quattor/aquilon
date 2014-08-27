# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
""" Virtual switches """

from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence, ForeignKey,
                        PrimaryKeyConstraint)
from sqlalchemy.orm import relation, backref, deferred

from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Base, Host, Cluster, PortGroup

_VS = 'virtual_switch'
_VSC = 'vswitch_cluster'
_VSH = 'vswitch_host'
_VSP = 'vswitch_pg'


class VirtualSwitch(Base):
    __tablename__ = _VS
    _class_label = 'Virtual Switch'

    id = Column(Integer, Sequence('%s_id_seq' % _VS), primary_key=True)

    name = Column(AqStr(63), nullable=False, unique=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    # Most of the update_* commands need to load the comments due to
    # snapshot_hw(), so it is not worth deferring it
    comments = Column(String(255), nullable=True)

    __table_args__ = {'info': {'unique_fields': ['name']}}


class __VSwitchClusterAssignment(Base):
    __tablename__ = _VSC

    virtual_switch_id = Column(Integer, ForeignKey(VirtualSwitch.id),
                               nullable=False)

    cluster_id = Column(Integer, ForeignKey(Cluster.id,
                                            ondelete='CASCADE'),
                        nullable=False, unique=True)

    __table_args__ = (PrimaryKeyConstraint(virtual_switch_id, cluster_id),)

VirtualSwitch.clusters = relation(Cluster,
                                  secondary=__VSwitchClusterAssignment.__table__,
                                  passive_deletes=True,
                                  backref=backref('virtual_switch',
                                                  uselist=False,
                                                  passive_deletes=True))


class __VSwitchHostAssignment(Base):
    __tablename__ = _VSH

    virtual_switch_id = Column(Integer, ForeignKey(VirtualSwitch.id),
                               nullable=False)

    host_id = Column(Integer, ForeignKey(Host.hardware_entity_id,
                                         ondelete='CASCADE'),
                     nullable=False, unique=True)

    __table_args__ = (PrimaryKeyConstraint(virtual_switch_id, host_id),)

VirtualSwitch.hosts = relation(Host,
                               secondary=__VSwitchHostAssignment.__table__,
                               passive_deletes=True,
                               backref=backref('virtual_switch', uselist=False,
                                               passive_deletes=True))


class __VSwitchPGAssignment(Base):
    __tablename__ = _VSP

    virtual_switch_id = Column(Integer, ForeignKey(VirtualSwitch.id,
                                                   ondelete='CASCADE'),
                               nullable=False)

    port_group_id = Column(Integer, ForeignKey(PortGroup.network_id,
                                               ondelete='CASCADE'),
                           nullable=False, index=True)

    __table_args__ = (PrimaryKeyConstraint(virtual_switch_id, port_group_id),)

VirtualSwitch.port_groups = relation(PortGroup,
                                     secondary=__VSwitchPGAssignment.__table__,
                                     passive_deletes=True,
                                     backref=backref('virtual_switches',
                                                     passive_deletes=True))
