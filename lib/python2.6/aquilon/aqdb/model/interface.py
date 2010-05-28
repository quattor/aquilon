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

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import relation, backref, validates, object_session
from sqlalchemy.sql.expression import desc, func

from aquilon.aqdb.column_types import AqMac, AqStr, Enum
from aquilon.aqdb.model import Base, System, HardwareEntity, ObservedMac

INTERFACE_TYPES = ('public', 'management', 'oa') #, 'transit')

def _validate_mac(kw):
    """ Prevents null MAC addresses in certain cases.

        If an interface is bootable or type 'management' we require it """

    msg = 'Bootable and Management interfaces require a MAC address'
    if kw.get('bootable') or kw.get('interface_type') == 'management':
        if kw.get('mac') is None:
            raise ValueError(msg)
    return True

class Interface(Base):
    """ In this design, interface is really just a name/type pair, AND the
        primary source for MAC address. Name/Mac/IP, the primary tuple, is
        in system, where mac is duplicated, but code to update MAC addresses
        must come through here """

    __tablename__ = 'interface'

    id = Column(Integer, Sequence('interface_seq'), primary_key=True)

    name = Column(AqStr(32), nullable=False) #like e0, hme1, etc.

    mac = Column(AqMac(17), nullable=True)

    bootable = Column(Boolean, nullable=False, default=False)

    interface_type = Column(Enum(32, INTERFACE_TYPES),
                            nullable=False) #TODO: index? Delete?

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name='IFACE_HW_ENT_FK',
                                                    ondelete='CASCADE'),
                                nullable=False)

    system_id = Column(Integer, ForeignKey('system.id',
                                           name='IFACE_SYSTEM_FK',
                                           ondelete='CASCADE'),
                       nullable=True)

    port_group = Column(AqStr(32), nullable=True)

    creation_date = Column('creation_date', DateTime, default=datetime.now,
                           nullable=False)

    comments = Column('comments', String(255), nullable=True)

    hardware_entity = relation(HardwareEntity, lazy=False,
                               backref=backref('interfaces'))

    system = relation(System, backref='interfaces')

    @validates('mac')
    def validate_mac(self, key, value):
        temp_dict = {'bootable': self.bootable, 'mac': value,
                     'interface_type': self.interface_type}
        _validate_mac(temp_dict)
        return value

    @property
    def last_observation(self):
        session = object_session(self)
        q = session.query(ObservedMac)
        q = q.filter_by(mac_address=self.mac)
        if session.connection().dialect.name == 'oracle':
            # Group the results into 'any port number but zero' and 'port 0'.
            # This prioritizes any port over the uplink port.
            # Saying that port 0 is an uplink port isn't very elegant...
            q = q.order_by(desc(func.DECODE(ObservedMac.port_number, 0, 0, 1)))
        q = q.order_by(desc(ObservedMac.last_seen))
        return q.first()

    def __init__(self, **kw): # pylint: disable-msg=E1002
        """ Overload the Base initializer to prevent null MAC addresses
            where the interface is bootable or is of type 'management'
        """
        _validate_mac(kw)
        super(Interface, self).__init__(**kw)

    def __str__(self):
        return 'Interface {0} for {1} {2}'.format(
            self.name, self.hardware_entity.hardware_entity_type,
            self.hardware_entity.hardware_name)

    #TODO: __repr__ when interface is simplified by dns changes

interface = Interface.__table__ # pylint: disable-msg=C0103, E1101
interface.primary_key.name = 'interface_pk'

interface.append_constraint(UniqueConstraint('mac', name='iface_mac_addr_uk'))

interface.append_constraint(
    UniqueConstraint('hardware_entity_id', 'name', name='iface_hw_name_uk'))