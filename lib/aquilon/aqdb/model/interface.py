# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Classes and Tables relating to network interfaces"""

from datetime import datetime
from collections import deque
import re

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint, CheckConstraint, Index)
from sqlalchemy.orm import (relation, backref, validates, object_session,
                            deferred)
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql import desc, case, and_, or_

from aquilon.exceptions_ import InternalError
from aquilon.aqdb.column_types import AqMac, AqStr
from aquilon.aqdb.model import (Base, HardwareEntity, DeviceLinkMixin,
                                ObservedMac, Model)
from aquilon.aqdb.model.vlan import MAX_VLANS

_TN = "interface"
_ABV = "iface"


class Interface(DeviceLinkMixin, Base):
    """ Interface: Representation of network interfaces for our network

        This table stores collections of machines, names, mac addresses,
        types, and a bootable flag to aid our DHCP and machine configuration.
    """

    __tablename__ = _TN

    # Any extra fields the subclass needs over the generic interface parameters
    extra_fields = []

    # Name syntax restrictions
    name_check = None

    # Allows setting model/vendor
    model_allowed = False

    # The Natural (and composite) pk is HW_ENT_ID/NAME.
    # But is it the "correct" pk in this case???. The surrogate key is here
    # only because it's easier to have a single target FK in the address
    # association object. It might actually be doable to use the natural key if
    # we try it. The upside: less clutter, meaningful keys. Downside:
    # It's also extra work we may not enjoy, it means rewriting the table
    # since we'd blow away its PK.

    id = Column(Integer, Sequence('%s_seq' % _TN), primary_key=True)

    name = Column(AqStr(32), nullable=False)  # like e0, hme1, etc.

    mac = Column(AqMac(17), nullable=True)

    model_id = Column(Integer, ForeignKey(Model.id,
                                          name='%s_model_fk' % _ABV),
                      nullable=False)

    # PXE boot control. Does not affect how the OS configures the interface.
    # FIXME: move to PublicInterface
    bootable = Column(Boolean(name="%s_bootable_ck" % _ABV), nullable=False,
                      default=False)

    default_route = Column(Boolean(name="%s_default_route_ck" % _ABV),
                           nullable=False, default=False)

    interface_type = Column(AqStr(32), nullable=False)

    hardware_entity_id = Column(Integer, ForeignKey(HardwareEntity.id,
                                                    name='%s_hw_ent_fk' % _ABV,
                                                    ondelete='CASCADE'),
                                nullable=False)

    # The FK is deferrable to make it easier to copy the DB between different
    # backends. The broker itself does not make use of deferred constraints.
    master_id = Column(Integer, ForeignKey(id, name='%s_master_fk' % _ABV,
                                           ondelete='CASCADE',
                                           deferrable=True,
                                           initially='IMMEDIATE'),
                       nullable=True)

    # FIXME: move to PublicInterface
    port_group = Column(AqStr(32), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    # Most of the update_* commands need to load the comments due to
    # snapshot_hw(), so it is not worth deferring it
    comments = Column('comments', String(255), nullable=True)

    hardware_entity = relation(HardwareEntity, lazy=False, innerjoin=True,
                               backref=backref('interfaces',
                                               cascade='all, delete-orphan'))

    model = relation(Model, innerjoin=True)

    master = relation('Interface',
                      remote_side=id,
                      primaryjoin=master_id == id,
                      backref=backref('slaves'))

    # Order matters here, utils/constraints.py checks for endswith("NOT NULL")
    __table_args__ = (UniqueConstraint(mac, name='%s_mac_addr_uk' % _ABV),
                      UniqueConstraint(hardware_entity_id, name,
                                       name='%s_hw_name_uk' % _ABV),
                      Index('%s_model_idx' % _ABV, model_id),
                      Index('%s_master_idx' % _ABV, master_id))
    __mapper_args__ = {'polymorphic_on': interface_type}

    # Interfaces also have the property 'assignments' which is defined in
    # address_assignment.py

    def __format__(self, format_spec):
        instance = "{0.name} of {1:l}".format(self, self.hardware_entity)
        return self.format_helper(format_spec, instance)

    @validates('mac')
    def _validate_mac(self, key, value):
        # Due to how decorators work, we have to do a level of indirection to
        # make polymorphism work
        return self.validate_mac(key, value)

    def validate_mac(self, key, value):
        if self.bootable and not value:
            raise ValueError("Bootable interfaces require a MAC address.")
        return value

    @validates('name')
    def validate_name(self, key, value):
        if self.__class__.name_check and \
           not self.__class__.name_check.match(value):
            raise ValueError("Illegal %s interface name '%s'." %
                             (self.interface_type, value))
        return value

    @validates('master')
    def validate_master(self, key, value):
        if value is not None and not isinstance(value, BondingInterface) and \
           not isinstance(value, BridgeInterface):
            raise ValueError("The master must be a bonding or bridge interface.")
        if self.vlans:
            raise ValueError("{0} can not be bound as long as it has "
                             "VLANs.".format(self))
        if self.assignments:
            raise ValueError("{0} cannot be enslaved as long as it holds "
                             "addresses.".format(self))
        return value

    @property
    def last_observation(self):
        session = object_session(self)
        q = session.query(ObservedMac)
        q = q.filter_by(mac_address=self.mac)
        # Group the results into 'any port number but zero' and 'port 0'.
        # This prioritizes any port over the uplink port.
        # Saying that port 0 is an uplink port isn't very elegant, also
        # with real port names it's not even true.
        q = q.order_by(desc(case([(ObservedMac.port == "0", 0)], else_=1)))
        q = q.order_by(desc(ObservedMac.last_seen))
        return q.first()

    def __init__(self, **kw):
        """ Overload the Base initializer to prevent null MAC addresses
            where the interface is bootable or is of type 'management'
        """
        super(Interface, self).__init__(**kw)
        self.validate_mac("mac", self.mac)

    def __repr__(self):
        msg = "<{0} {1} of {2}, MAC={3}>".format(self._get_class_label(),
                                                 self.name,
                                                 self.hardware_entity, self.mac)
        return msg

    def all_slaves(self):
        queue = deque(self.slaves)
        slaves = []
        while queue:
            iface = queue.popleft()
            slaves.append(iface)
            queue.extend(iface.slaves)
        return slaves


class PublicInterface(Interface):
    """ Normal machine interfaces """

    _class_label = "Public Interface"

    __mapper_args__ = {'polymorphic_identity': 'public'}

    extra_fields = ['bootable', 'port_group']

    name_check = re.compile(r"^[a-z]+\d+[a-z]?$")

    model_allowed = True


class ManagementInterface(Interface):
    """ Management board interfaces """

    _class_label = "Management Interface"

    __mapper_args__ = {'polymorphic_identity': 'management'}

    name_check = re.compile(r"^[a-z]+\d*$")

    def validate_mac(self, key, value):
        if not value:
            raise ValueError("Management interfaces require a MAC address.")
        return value


class OnboardInterface(Interface):
    """ Switch/chassis interfaces """

    _class_label = "On-board Admin Interface"

    __mapper_args__ = {'polymorphic_identity': 'oa'}

    # There are interface names like "gigabitethernet0/1", so no name checks for
    # now.


class VlanInterface(Interface):
    """ 802.1q VLAN interfaces """

    _class_label = "VLAN Interface"

    extra_fields = ['vlan_id', 'parent']

    name_check = re.compile(r"^[a-z]+\d*\.[1-9]\d*$")

    # The FK is deferrable to make it easier to copy the DB between different
    # backends. The broker itself does not make use of deferred constraints.
    parent_id = Column(Integer, ForeignKey(Interface.id,
                                           name='iface_vlan_parent_fk',
                                           ondelete='CASCADE',
                                           deferrable=True,
                                           initially='IMMEDIATE'))

    vlan_id = Column(Integer)

    parent = relation(Interface,
                      remote_side=Interface.id,
                      primaryjoin=parent_id == Interface.id,
                      backref=backref('vlans',
                                      collection_class=attribute_mapped_collection('vlan_id')))

    __mapper_args__ = {'polymorphic_identity': 'vlan'}
    # Order matters here, utils/constraints.py checks for endswith("NOT NULL")
    __extra_table_args__ = (CheckConstraint(or_(and_(parent_id != None,
                                                     vlan_id > 0,
                                                     vlan_id < MAX_VLANS),
                                                Interface.interface_type != "vlan"),
                                            name="%s_vlan_ck" % _ABV),
                            UniqueConstraint(parent_id, vlan_id,
                                             name="%s_parent_vlan_uk" % _ABV))

    @validates('vlan_id')
    def validate_vlan_id(self, key, value):
        if not isinstance(value, int) or value <= 0 or value >= MAX_VLANS:
            raise ValueError("Illegal VLAN ID %s: it must be greater than "
                             "0 and smaller than %s." % (value, MAX_VLANS))
        return value

    def validate_mac(self, key, value):
        if value is not None:
            raise ValueError("VLAN interfaces can not have a distinct MAC address.")
        return value

    def __init__(self, parent=None, vlan_id=None, **kwargs):
        if not parent:
            raise InternalError("VLAN interfaces need a parent.")
        if isinstance(parent, VlanInterface):
            raise ValueError("Stacking of VLAN interfaces is not allowed.")
        self.validate_vlan_id('vlan_id', vlan_id)

        super(VlanInterface, self).__init__(parent=parent, vlan_id=vlan_id,
                                            **kwargs)


class BondingInterface(Interface):
    """ Channel bonding interfaces """

    _class_label = "Bonding Interface"

    __mapper_args__ = {'polymorphic_identity': 'bonding'}

    # Linux: ncm-networks wans "bond.*", but Netapp is more relaxed
    name_check = re.compile(r'^[a-z]+\d+$')


class BridgeInterface(Interface):
    """ Level 2 bridge interfaces """

    _class_label = "Bridge Interface"

    __mapper_args__ = {'polymorphic_identity': 'bridge'}

    # Bridges on Linux could have any random name, but the templates also
    # enforce this naming
    name_check = re.compile(r'^br\d+$')

    def validate_mac(self, key, value):
        if value is not None:
            raise ValueError("Bridge interfaces can not have a distinct MAC address.")
        return value


class LoopbackInterface(Interface):
    """ Virtual loopback interface, primarily for switches """

    _class_label = "Loopback Interface"

    __mapper_args__ = {'polymorphic_identity': 'loopback'}

    def validate_mac(self, key, value):
        if value is not None:
            raise ValueError("Loopback interfaces cannot have a MAC address.")
        return value


class VirtualInterface(Interface):
    """ Network device virtual interface """

    _class_label = "Virtual Interface"

    __mapper_args__ = {'polymorphic_identity': 'virtual'}


class PhysicalInterface(Interface):
    """ Network device physical interface """

    _class_label = "Physical Interface"

    __mapper_args__ = {'polymorphic_identity': 'physical'}


interface = Interface.__table__  # pylint: disable=C0103
interface.info['unique_fields'] = ['name', 'hardware_entity']
interface.info['extra_search_fields'] = ['mac']
