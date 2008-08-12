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

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Column, Table, Integer, Sequence, String, Index,
                        Boolean, CheckConstraint, UniqueConstraint, DateTime,
                        ForeignKey, PrimaryKeyConstraint, insert, select )

from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.column_types.aqstr  import AqStr
from aquilon.aqdb.db_factory          import Base
from aquilon.aqdb.hw.interface        import Interface
from aquilon.aqdb.loc.location        import Location
from aquilon.aqdb.loc.chassis         import Chassis
from aquilon.aqdb.hw.machine          import Machine

#maybe this is an association object as opposed to an inheritance relationship?
# interface -> m2m -> machine
# interface -> m2m -> network_device

class PhysicalInterface(Interface):
    """ Class to model up the physical nic cards/devices in machines """
    __tablename__ = 'physical_interface'

    interface_id = Column(Integer, ForeignKey(
        'interface.id', name = 'phys_int_int_fk', ondelete='CASCADE'),
                          primary_key=True)

    machine_id = Column(Integer, ForeignKey(
        'machine.id', name = 'PHYS_IFACE_MACH_ID_FK',ondelete = 'CASCADE'),
                        nullable = False)

    name = Column(AqStr(32), nullable = False) #like e0, hme1, etc.
    #mac moved to "Interface" for expansion to network hw
    boot = Column(Boolean, nullable = False, default = False)

    machine   = relation(Machine, backref = 'interfaces',
                         passive_deletes = True)

    interface = relation(Interface, lazy = False,
                         uselist = False, backref = 'physical_interface',
                         passive_deletes = True)

    __mapper_args__ = {'polymorphic_identity' : 'physical' }

physical_interface = PhysicalInterface.__table__
physical_interface.primary_key.name = 'phys_iface_pk'

physical_interface.append_constraint(
    UniqueConstraint('machine_id', 'name',name = 'phys_iface_uk'))

Index('idx_phys_int_machine_id', physical_interface.c.machine_id)

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    physical_interface.create(checkfirst = True)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
