# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
""" The classes pertaining to VLAN info"""

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, ForeignKey, CheckConstraint,
                        UniqueConstraint)
from sqlalchemy.orm import relation, backref, object_session, aliased
from sqlalchemy.sql.expression import asc

from aquilon.exceptions_ import NotFoundException, InternalError
from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.aqdb.model import Base, Network, TorSwitch, Machine

MAX_VLANS = 4096 #IEEE 802.1Q standard

VLAN_TYPES = ('storage', 'vmotion', 'user')

VLAN_INFO = [(701, 'storage-v701', 'storage'),
             (702, 'vmotion-v702', 'vmotion'),
             (710, 'user-v710', 'user'), (711, 'user-v711', 'user'),
             (712, 'user-v712', 'user'), (713, 'user-v713', 'user')]

_VTN = 'vlan_info'


class VlanInfo(Base):
    """ information regarding well-known/standardized vlans """
    __tablename__ = _VTN

    vlan_id = Column(Integer, primary_key=True)
    port_group = Column(AqStr(32), nullable=False)
    vlan_type = Column(Enum(32, VLAN_TYPES), nullable=False)

    @classmethod
    def get_vlan_id(cls, session, port_group, compel=InternalError):
        info = session.query(cls).filter_by(port_group=port_group).first()
        if not info and compel:
            raise compel("No VLAN found for port group %s" % port_group)
        return info.vlan_id

    @classmethod
    def get_port_group(cls, session, vlan_id, compel=InternalError):
        info = session.query(cls).filter_by(vlan_id=vlan_id).first()
        if not info and compel:
            raise compel("No port group found for VLAN id %s" % vlan_id)
        return info.port_group

    def __repr__(self):
        return '<%s vlan_id=%s port_group=%s vlan_type=%s>' % (
            self.__class__.__name__, self.vlan_id, self.port_group,
            self.vlan_type)

VlanInfo.__table__.primary_key.name = '%s_pk' % _VTN
VlanInfo.__table__.append_constraint(
    UniqueConstraint('port_group', name='%s_port_group_uk' % _VTN))

#CheckConstraint doesn't upper case names by default
VlanInfo.__table__.append_constraint(
    CheckConstraint(('"vlan_id" < %s' % MAX_VLANS).upper(),
                    name=('%s_max_vlan_id' % _VTN).upper()))

@monkeypatch(VlanInfo.__table__)
def populate(sess, **kw):
    if sess.query(VlanInfo).count() == 0:
        for i in VLAN_INFO:
            vinfo = VlanInfo(vlan_id=i[0], port_group=i[1], vlan_type=i[2])
            sess.add(vinfo)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            print e

_TN = 'observed_vlan'
_ABV = 'obs_vlan'


class ObservedVlan(Base):
    """ reports the observance of a vlan/network on a switch """
    __tablename__ = 'observed_vlan'

    switch_id = Column(Integer, ForeignKey('tor_switch.id',
                                           ondelete='CASCADE',
                                           name='%s_hw_fk' % _ABV),
                       primary_key=True)

    network_id = Column(Integer, ForeignKey('network.id',
                                            ondelete='CASCADE',
                                            name='%s_net_fk' % _ABV),
                        primary_key=True)

    vlan_id = Column(Integer, primary_key=True)

    creation_date = Column('creation_date', DateTime,
                           default=datetime.now, nullable=False)

    switch = relation(TorSwitch, backref=backref('%ss' % _TN, cascade='delete',
                                                 order_by=[asc('vlan_id')]))
    network = relation(Network, backref=backref('%ss' % _TN, cascade='delete',
                                                order_by=[asc('vlan_id')]))

    @property
    def port_group(self):
        session = object_session(self)
        info = session.query(VlanInfo).filter_by(vlan_id=self.vlan_id).first()
        if info:
            return info.port_group
        return None

    @property
    def vlan_type(self):
        session = object_session(self)
        info = session.query(VlanInfo).filter_by(vlan_id=self.vlan_id).first()
        if info:
            return info.vlan_type
        return None

    @property
    def guest_count(self):
        # Can't import this earlier due to circular dependencies...
        from aquilon.aqdb.model import Cluster, EsxCluster
        # Count the number of VMs in the clusters with this switch and vlan.
        session = object_session(self)
        port_group = VlanInfo.get_port_group(session, vlan_id=self.vlan_id)
        ESXAlias = aliased(EsxCluster)
        q = session.query(Machine)
        q = q.join(['_cluster', 'cluster',
                    (ESXAlias, ESXAlias.esx_cluster_id == Cluster.id)])
        q = q.filter_by(switch=self.switch)
        q = q.reset_joinpoint()
        q = q.join(['interfaces'])
        q = q.filter_by(port_group=port_group)
        q = q.reset_joinpoint()
        return q.count()

    @property
    def is_at_guest_capacity(self):
        return self.guest_count >= self.network.available_ip_count

    @classmethod
    def get_network(cls, session, switch, vlan_id, compel=NotFoundException):
        q = session.query(cls).filter_by(switch=switch, vlan_id=vlan_id)
        nets = q.all()
        if not nets:
            raise compel("No network found for switch %s and VLAN %s" %
                         (switch.fqdn, vlan_id))
        if len(nets) > 1:
            raise InternalError("More than one network found for switch %s "
                                "and VLAN %s" % (switch.fqdn, vlan_id))
        return nets[0].network

ObservedVlan.__table__.primary_key.name = '%s_pk' % _TN

#CheckConstraint doesn't upper case names by default
ObservedVlan.__table__.append_constraint(
    CheckConstraint(('"vlan_id" < %s' % MAX_VLANS).upper(),
                    name=('%s_max_vlan_id' % _TN).upper()))
