#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" ChassisSlot sets up a structure for tracking position within a chassis. """
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.hw.machine import Machine
from aquilon.aqdb.sy.chassis import Chassis


class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = 'chassis_slot'

    chassis_id = Column(Integer,
                        ForeignKey('chassis.id',
                                   name='chassis_slot_chassis_fk',
                                   ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer,
                        ForeignKey('machine.id',
                                   name='chassis_slot_machine_fk'),
                        nullable=True)

    chassis = relation(Chassis, uselist=False,
                       backref=backref('slots', cascade='delete'),
                       passive_deletes=True)

    machine = relation(Machine, uselist=False,
                       backref=backref('chassis_slot'))

chassis_slot = ChassisSlot.__table__
chassis_slot.primary_key.name = 'chassis_slot_pk'

table = chassis_slot

def populate(db, *args, **kw):

    if len(db.s.query(ChassisSlot).all()) < 1:
        for c in db.s.query(Chassis).all():
            for node in range(1, 17):
                a = ChassisSlot(chassis=c, slot_number=node)
                db.s.add(a)
        db.s.commit()
        print 'created %d chassis slots' % db.s.query(ChassisSlot).count()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
