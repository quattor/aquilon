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

from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import relation #, synonym

from aquilon.aqdb.column_types import AqMac, AqStr
from aquilon.aqdb.model import Base, System, HardwareEntity


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

    interface_type = Column(AqStr(32), nullable=False) #TODO: index or delete

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

    hardware_entity = relation(HardwareEntity, backref='interfaces',
                               passive_deletes=True)

    system = relation(System, backref='interfaces', passive_deletes=True)

    # This is experimental code which will code in use later on
    # remember to change the column name to mymac above, also in unique index
    # below the class definition
    #def _get_mac(self):
    #    return self.mymac
    #
    #def _set_mac(self, mac=None):
    #    if self.bootable == True and mac is None:
    #        msg = 'Bootable interfaces require a MAC address'
    #        raise ArgumentError(msg)
    #    self.mymac=mac
    #
    #mac = synonym('mymac', descriptor=property(_get_mac, _set_mac))

    def __init__(self, **kw): # pylint: disable-msg=E1002
        """ Overload the Base initializer to prevent null MAC addresses
            where the interface is bootable
        """

        if 'bootable' in kw and kw['bootable'] == True:
            if not kw['mac']:
                msg = 'Bootable interfaces require a MAC address'
                raise ValueError(msg)
        super(Interface, self).__init__(**kw)

    # We'll need seperate python classes for each subtype if we want to
    # use single table inheritance like this.
    #__mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__ # pylint: disable-msg=C0103, E1101
interface.primary_key.name = 'interface_pk'

interface.append_constraint(UniqueConstraint('mac', name='iface_mac_addr_uk'))

interface.append_constraint(
    UniqueConstraint('hardware_entity_id', 'name', name='iface_hw_name_uk'))

table = interface # pylint: disable-msg=C0103
