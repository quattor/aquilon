# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015  Contributor
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
""" The classes pertaining to VLAN info"""

from datetime import datetime
import re

from sqlalchemy import (Column, Integer, DateTime, ForeignKey, CheckConstraint,
                        PrimaryKeyConstraint, Index, Sequence)
from sqlalchemy.orm import relation, backref, deferred
from sqlalchemy.sql import and_

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.column_types import AqStr
from aquilon.aqdb.model import Base, Network, NetworkDevice

MAX_VLANS = 4096  # IEEE 802.1Q standard

pg_re = re.compile(r'^(.*)-v(\d+)$')

_TN = 'observed_vlan'
_VTN = 'vlan_info'
_PG = 'port_group'


class VlanInfo(Base):
    """ information regarding well-known/standardized vlans """
    __tablename__ = _VTN
    _instance_label = 'vlan_id'

    vlan_id = Column(Integer, primary_key=True, autoincrement=False)
    port_group = Column(AqStr(32), nullable=False, unique=True)
    vlan_type = Column(AqStr(32), nullable=False)

    __table_args__ = (CheckConstraint(and_(vlan_id >= 0,
                                           vlan_id < MAX_VLANS),
                                      name='%s_vlan_id_ck' % _VTN),
                      {'info': {'unique_fields': ['port_group'],
                                'extra_search_fields': ['vlan_id']}})

    @classmethod
    def get_by_pg(cls, session, port_group, compel=InternalError):
        info = session.query(cls).filter_by(port_group=port_group).first()
        if not info and compel:
            raise compel("No VLAN found for port group %s." % port_group)
        return info

    @classmethod
    def get_by_vlan(cls, session, vlan_id, compel=InternalError):
        info = session.query(cls).filter_by(vlan_id=vlan_id).first()
        if not info and compel:
            raise compel("No port group found for VLAN id %s." % vlan_id)
        return info

    def __repr__(self):
        return '<%s vlan_id=%s port_group=%s vlan_type=%s>' % (
            self.__class__.__name__, self.vlan_id, self.port_group,
            self.vlan_type)


# TODO: eventually this class should be moved to a different file
class PortGroup(Base):
    __tablename__ = _PG
    _class_label = 'Port Group'

    id = Column(Integer, Sequence("%s_id_seq" % _PG), primary_key=True)

    network_id = Column(ForeignKey(Network.id, ondelete='CASCADE'),
                        nullable=False, unique=True)

    # VLAN or VxLAN ID
    network_tag = Column(Integer, nullable=False)

    usage = Column(AqStr(32), nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    __table_args__ = (Index("%s_usage_tag_idx" % _PG, usage, network_tag,
                            oracle_compress=1),)

    network = relation(Network, innerjoin=True,
                       backref=backref('port_group', uselist=False,
                                       passive_deletes=True))

    # This is needed only for legacy naming
    legacy_vlan = relation(VlanInfo, uselist=False,
                           primaryjoin=and_(usage == VlanInfo.vlan_type,
                                            network_tag == VlanInfo.vlan_id),
                           foreign_keys=[VlanInfo.vlan_type, VlanInfo.vlan_id],
                           viewonly=True)

    @property
    def name(self):
        if self.legacy_vlan:
            return self.legacy_vlan.port_group
        else:
            return "%s-v%d" % (self.usage, self.network_tag)

    @classmethod
    def parse_name(cls, name):
        match = pg_re.match(name)
        if match:
            return (match.group(1), int(match.group(2)))
        else:
            return (None, None)


class __ObservedVlan(Base):
    """ reports the observance of a vlan/network on a switch """
    __tablename__ = _TN

    network_device_id = Column(ForeignKey(NetworkDevice.hardware_entity_id,
                                          ondelete='CASCADE'),
                               nullable=False)

    port_group_id = Column(ForeignKey(PortGroup.id, ondelete='CASCADE'),
                           nullable=False, index=True)

    __table_args__ = (PrimaryKeyConstraint(network_device_id, port_group_id),)

NetworkDevice.port_groups = relation(PortGroup,
                                     secondary=__ObservedVlan.__table__,
                                     cascade="save-update, merge",
                                     backref=backref('network_devices'))
