# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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
from sqlalchemy.orm import relation, backref

from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types import AqStr, Enum
from aquilon.aqdb.model import Base, Network, TorSwitch

MAX_VLANS = 4096 #IEEE 802.1Q standard

VLAN_TYPES = ('storage', 'vmotion', 'vmnet')

VLAN_INFO = [(700, 'storage', 'storage'), (701, 'vmotion', 'vmotion'),
    (710, 'vmnet_1', 'vmnet'), (711, 'vmnet_2', 'vmnet'),
    (712, 'vmnet_3', 'vmnet'), (714, 'vmnet_4', 'vmnet')]

_VTN = 'vlan_info'


class VlanInfo(Base):
    """ information regarding well-known/standardized vlans """
    __tablename__ = _VTN

    vlan_id = Column(Integer, primary_key=True)
    port_group = Column(AqStr(32))
    vlan_type = Column(Enum(32, VLAN_TYPES))

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

    switch = relation(TorSwitch, backref=backref('%ss' % _TN, cascade='delete'))
    network = relation(Network, backref=backref('%ss' % _TN, cascade='delete'))

    #TODO: vlan_info as query mapped property?
    @property
    def portgroup(self):
        session = object_session(self)
        info = session.query(VlanInfo).filter_by(vlan_id=self.vlan_id).first()
        if info:
            return info.port_group
        return None

ObservedVlan.__table__.primary_key.name = '%s_pk' % _TN

#CheckConstraint doesn't upper case names by default
ObservedVlan.__table__.append_constraint(
    CheckConstraint(('"vlan_id" < %s' % MAX_VLANS).upper(),
                    name=('%s_max_vlan_id' % _TN).upper()))
