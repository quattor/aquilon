# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014  Contributor
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

from sqlalchemy import (Column, Integer, DateTime, ForeignKey, CheckConstraint,
                        UniqueConstraint, PrimaryKeyConstraint, Index)
from sqlalchemy.orm import relation, backref, deferred, object_session
from sqlalchemy.sql import func, and_

from aquilon.exceptions_ import NotFoundException, InternalError
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.aqdb.model import Base, Network, NetworkDevice

MAX_VLANS = 4096  # IEEE 802.1Q standard

VLAN_TYPES = ('storage', 'vmotion', 'user', 'unknown', 'vulcan-mgmt', 'vcs')

_TN = 'observed_vlan'
_ABV = 'obs_vlan'
_VTN = 'vlan_info'


class VlanInfo(Base):
    """ information regarding well-known/standardized vlans """
    __tablename__ = _VTN
    _instance_label = 'vlan_id'

    vlan_id = Column(Integer, primary_key=True, autoincrement=False)
    port_group = Column(AqStr(32), nullable=False)
    vlan_type = Column(Enum(32, VLAN_TYPES), nullable=False)

    __table_args__ = (UniqueConstraint(port_group,
                                       name='%s_port_group_uk' % _VTN),
                      CheckConstraint(and_(vlan_id >= 0,
                                           vlan_id < MAX_VLANS),
                                      name='%s_vlan_id_ck' % _VTN))

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

vlaninfo = VlanInfo.__table__  # pylint: disable=C0103
vlaninfo.info['unique_fields'] = ['port_group']
vlaninfo.info['extra_search_fields'] = ['vlan_id']


class ObservedVlan(Base):
    """ reports the observance of a vlan/network on a switch """
    __tablename__ = 'observed_vlan'

    network_device_id = Column(Integer,
                               ForeignKey('network_device.hardware_entity_id',
                                          ondelete='CASCADE',
                                          name='%s_hw_fk' % _ABV),
                               nullable=False)

    network_id = Column(Integer, ForeignKey('network.id',
                                            ondelete='CASCADE',
                                            name='%s_net_fk' % _ABV),
                        nullable=False)

    vlan_id = Column(Integer, ForeignKey('vlan_info.vlan_id',
                                         name='%s_vlan_fk' % _ABV),
                     nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    network_device = relation(NetworkDevice, innerjoin=True,
                              backref=backref('%ss' % _TN, cascade='delete',
                                              passive_deletes=True,
                                              order_by=[vlan_id]))
    network = relation(Network, innerjoin=True,
                       backref=backref('%ss' % _TN, cascade='delete',
                                       passive_deletes=True,
                                       order_by=[vlan_id]))

    vlan = relation(VlanInfo, uselist=False,
                    primaryjoin=vlan_id == VlanInfo.vlan_id,
                    foreign_keys=[VlanInfo.vlan_id],
                    viewonly=True)

    __table_args__ = (PrimaryKeyConstraint(network_device_id, network_id, vlan_id,
                                           name="%s_pk" % _TN),
                      CheckConstraint(and_(vlan_id >= 0,
                                           vlan_id < MAX_VLANS),
                                      name='%s_vlan_id_ck' % _TN),
                      Index('%s_network_idx' % _TN, 'network_id'),
                      Index('%s_vlan_idx' % _TN, 'vlan_id'))

    @property
    def port_group(self):
        if self.vlan:
            return self.vlan.port_group
        return None

    @property
    def vlan_type(self):
        if self.vlan:
            return self.vlan.vlan_type
        return None

    @property
    def guest_count(self):
        from aquilon.aqdb.model import (EsxCluster, Cluster, ClusterResource,
                                        Resource, VirtualMachine, Machine,
                                        HardwareEntity, Interface)
        session = object_session(self)
        q = session.query(func.count())
        q = q.filter(and_(
            # Select VMs on clusters that belong to the given switch
            EsxCluster.network_device_id == self.network_device_id,
            Cluster.id == EsxCluster.esx_cluster_id,
            ClusterResource.cluster_id == Cluster.id,
            Resource.holder_id == ClusterResource.id,
            VirtualMachine.resource_id == Resource.id,
            Machine.machine_id == VirtualMachine.machine_id,
            # Select interfaces with the right port group
            HardwareEntity.id == Machine.machine_id,
            Interface.hardware_entity_id == HardwareEntity.id,
            Interface.port_group == VlanInfo.port_group,
            VlanInfo.vlan_id == self.vlan_id))
        return q.scalar()

    @classmethod
    def get_network(cls, session, network_device, vlan_id, compel=NotFoundException):
        q = session.query(cls).filter_by(network_device=network_device, vlan_id=vlan_id)
        nets = q.all()
        if not nets:
            raise compel("No network found for switch %s and VLAN %s" %
                         (network_device.fqdn, vlan_id))
        if len(nets) > 1:
            raise InternalError("More than one network found for switch %s "
                                "and VLAN %s" % (network_device.fqdn, vlan_id))
        return nets[0].network
