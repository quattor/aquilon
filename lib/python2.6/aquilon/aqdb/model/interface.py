# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Classes and Tables relating to network interfaces"""

#Note: any changes to this class definition and it's constraints
#should always be reviewed by DHCP Eng.

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, Boolean,
                        ForeignKey, UniqueConstraint, CheckConstraint)
from sqlalchemy.orm import relation, backref, validates, object_session
from sqlalchemy.orm.collections import attribute_mapped_collection
from sqlalchemy.sql.expression import desc, case

from aquilon.aqdb.column_types import AqMac, AqStr, Enum
from aquilon.aqdb.model import Base, HardwareEntity, ObservedMac

from aquilon.aqdb.model.vlan import MAX_VLANS


class Interface(Base):
    """ Interface: Representation of network interfaces for our network

        This table stores collections of machines, names, mac addresses,
        types, and a bootable flag to aid our DHCP and machine configuration.
    """

    __tablename__ = 'interface'

    # The Natural (and composite) pk is HW_ENT_ID/NAME.
    # But is it the "correct" pk in this case???. The surrogate key is here
    # only because it's easier to have a single target FK in the address
    # association object. It might actually be doable to use the natural key if
    # we try it. The upside: less clutter, meaningful keys. Downside:
    # It's also extra work we may not enjoy, it means rewriting the table
    # since we'd blow away its PK.

    id = Column(Integer, Sequence('interface_seq'), primary_key=True)

    name = Column(AqStr(32), nullable=False) #like e0, hme1, etc.

    mac = Column(AqMac(17), nullable=True)

    # PXE boot control. Does not affect how the OS configures the interface.
    # FIXME: move to PublicInterface
    bootable = Column(Boolean, nullable=False, default=False)

    interface_type = Column(AqStr(32), nullable=False)

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='IFACE_HW_ENT_FK',
                                                    ondelete='CASCADE'),
                                nullable=False)

    # FIXME: move to PublicInterface
    port_group = Column(AqStr(32), nullable=True)

    creation_date = Column('creation_date', DateTime, default=datetime.now,
                           nullable=False)

    comments = Column('comments', String(255), nullable=True)

    hardware_entity = relation(HardwareEntity, lazy=False, innerjoin=True,
                               backref=backref('interfaces', cascade='all'))

    __mapper_args__ = {'polymorphic_on': interface_type}
    # Interfaces also have the property 'assignments' which is defined in
    # address_assignment.py

    def __format__(self, format_spec):
        instance = "{0.name} of {1:l}".format(self, self.hardware_entity)
        return self.format_helper(format_spec, instance)

    @validates('mac')
    def validate_mac(self, key, value):
        if self.bootable and not value:
            raise ValueError("Bootable interfaces require a MAC address.")
        return value

    @property
    def last_observation(self):
        session = object_session(self)
        q = session.query(ObservedMac)
        q = q.filter_by(mac_address=self.mac)
        # Group the results into 'any port number but zero' and 'port 0'.
        # This prioritizes any port over the uplink port.
        # Saying that port 0 is an uplink port isn't very elegant...
        q = q.order_by(desc(case([(ObservedMac.port_number == 0, 0)], else_=1)))
        q = q.order_by(desc(ObservedMac.last_seen))
        return q.first()

    def all_addresses(self):
        """ Iterator returning all addresses of the interface. """
        for addr in self.assignments:
            yield addr

    def __init__(self, **kw):  # pylint: disable-msg=E1002
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


class PublicInterface(Interface):
    """ Normal machine interfaces """

    _class_label = "Public Interface"

    __mapper_args__ = {'polymorphic_identity': 'public'}


class ManagementInterface(Interface):
    """ Management board interfaces """

    _class_label = "Management Interface"

    __mapper_args__ = {'polymorphic_identity': 'management'}

    @validates('mac')
    def validate_mac(self, key, value):
        if not value:
            raise ValueError("Management interfaces require a MAC address.")
        return value


class  OnboardInterface(Interface):
    """ Switch/chassis interfaces """

    _class_label = "On-board Admin Interface"

    __mapper_args__ = {'polymorphic_identity': 'oa'}


class VlanInterface(Interface):
    """ 802.1q VLAN interfaces """

    _class_label = "VLAN Interface"

    __mapper_args__ = {'polymorphic_identity': 'vlan'}

    parent_id = Column(Integer, ForeignKey(Interface.id,
                                           name='iface_vlan_parent_fk',
                                           ondelete='CASCADE'))

    vlan_id = Column(Integer)

    parent = relation(Interface, uselist=False, lazy=True,
                      remote_side=[Interface.id],
                      backref=backref('vlans',
                                      collection_class=attribute_mapped_collection('vlan_id')))

    @validates('vlan_id')
    def validate_vlan_id(self, key, value):
        if not isinstance(value, int) or value <= 0 or value >= MAX_VLANS:
            raise ValueError("Illegal VLAN ID %s: it must be greater than "
                             "0 and smaller than %s." % (value, MAX_VLANS))
        return value

    @validates('mac')
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


interface = Interface.__table__  # pylint: disable-msg=C0103, E1101
interface.primary_key.name = 'interface_pk'
interface.info['unique_fields'] = ['name', 'hardware_entity']

interface.append_constraint(UniqueConstraint('mac', name='iface_mac_addr_uk'))

interface.append_constraint(
    UniqueConstraint('hardware_entity_id', 'name', name='iface_hw_name_uk'))

# Order matters here, utils/constraints.py checks for endswith("NOT NULL")
interface.append_constraint(
    CheckConstraint("(parent_id IS NOT NULL AND vlan_id > 0 AND vlan_id < %s) "
                    "OR interface_type <> 'vlan'" % MAX_VLANS,
                    name="iface_vlan_ck"))
interface.append_constraint(
    UniqueConstraint('parent_id', 'vlan_id', name="iface_parent_vlan_uk"))
