#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Classes and Tables relating to network interfaces"""
import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0, os.path.join(DIR, '..'))

import depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, PrimaryKeyConstraint, insert, select )

from sqlalchemy.orm import relation, deferred

from column_types.aqstr  import AqStr
from db_factory          import Base
from interface           import Interface
from loc.location        import Location
from loc.chassis         import Chassis
from hw.machine          import Machine

class PhysicalInterface(Interface):
    """ Class to model up the physical nic cards/devices in machines """
    __tablename__ = 'physical_interface'

    id = Column(Integer, ForeignKey('interface.id',
                                    ondelete='CASCADE'), primary_key=True)
    machine_id = Column(Integer,
                        ForeignKey('machine.id', ondelete='CASCADE'),
                        nullable=False)

    name = Column(AqStr(32), nullable = False) #like e0, hme1, etc.
    mac  = Column(AqStr(32), nullable = False)
    boot = Column(Boolean, nullable = False, default = False)

    machine   = relation(Machine, backref = 'interfaces')
    interface = relation(Interface, lazy = False,
                         uselist = False, backref = 'physical_interface')

    __mapper_args__ = {'polymorphic_identity' : 'physical' }

physical_interface = PhysicalInterface.__table__
physical_interface.primary_key.name = 'phy_iface_pk'

physical_interface.append_constraint(
    UniqueConstraint('mac',name='mac_addr_uk'))

physical_interface.append_constraint(
    UniqueConstraint('machine_id','name',name='phy_iface_uk'))

Index('idx_phys_int_machine_id', physical_interface.c.machine_id)

#TODO: column type for MAC
#reg = re.compile('^([a-f0-9]{2,2}:){5,5}[a-f0-9]{2,2}$')
#if (not reg.match(self.mac)):
#    raise ArgumentError ('Invalid MAC address: '+self.mac)

#TODO: another oddity in the old __init__
#self.name == 'e0':
#            self.boot=True

def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    physical_interface.create(checkfirst = True)
