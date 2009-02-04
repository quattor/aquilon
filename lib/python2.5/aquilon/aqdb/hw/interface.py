"""Classes and Tables relating to network interfaces"""

from datetime import datetime

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, PrimaryKeyConstraint, insert, select)
from sqlalchemy.orm import mapper, relation, deferred

from aquilon.aqdb.base import Base
from aquilon.aqdb.column_types.aqmac import AqMac
from aquilon.aqdb.column_types.aqstr import AqStr
from aquilon.aqdb.sy.system          import System
from aquilon.aqdb.hw.hardware_entity import HardwareEntity

class Interface(Base):
    """ In this design, interface is really just a name/type pair, AND the
        primary source for MAC address. Name/Mac/IP, the primary tuple, is
        in system, where mac is duplicated, but code to update MAC addresses
        must come through here """

    __tablename__ = 'interface'

    id   = Column(Integer, Sequence('interface_seq'), primary_key=True)

    name = Column(AqStr(32), nullable=False) #like e0, hme1, etc.

    mac  = Column(AqMac(17), nullable=False)

    bootable           = Column(Boolean, nullable=False, default=False)

    interface_type     = Column(AqStr(32), nullable=False) #TODO: index

    hardware_entity_id = Column(Integer, ForeignKey('hardware_entity.id',
                                                    name = 'IFACE_HW_ENT_FK',
                                                    ondelete = 'CASCADE'),
                                                   nullable = False)

    system_id          = Column(Integer, ForeignKey('system.id',
                                                 name = 'IFACE_SYSTEM_FK',
                                                 ondelete = 'CASCADE'),
                                                nullable = True)

    creation_date      = deferred(Column('creation_date', DateTime,
                                       default = datetime.now,
                                     nullable = False))

    comments           = deferred(Column('comments',String(255)))

    hardware_entity    = relation(HardwareEntity, backref = 'interfaces',
                             passive_deletes = True)

    system             = relation(System, backref = 'interfaces',
                               passive_deletes = True)

    # We'll need seperate python classes for each subtype if we want to
    # use single table inheritance like this.
    #__mapper_args__ = {'polymorphic_on' : interface_type}

interface = Interface.__table__
interface.primary_key.name = 'interface_pk'

interface.append_constraint(
        UniqueConstraint('mac', name = 'iface_mac_addr_uk'))

interface.append_constraint(
        UniqueConstraint('hardware_entity_id', 'name', name = 'iface_hw_name_uk'))

table = interface


# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
