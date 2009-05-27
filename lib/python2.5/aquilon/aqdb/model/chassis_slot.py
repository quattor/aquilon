""" ChassisSlot sets up a structure for tracking position within a chassis. """

from sqlalchemy import Column, Integer, ForeignKey
from sqlalchemy.orm import relation, backref
from sqlalchemy.sql.expression import asc

from aquilon.aqdb.model import Base, Machine, Chassis

class ChassisSlot(Base):
    """ ChassisSlot allows a Machine to be assigned to each unique position
        within a Chassis. """

    __tablename__ = 'chassis_slot'

    chassis_id = Column(Integer,
                        ForeignKey('chassis.system_id',
                                   name='chassis_slot_chassis_fk',
                                   ondelete='CASCADE'),
                        primary_key=True)

    slot_number = Column(Integer, primary_key=True)

    # TODO: Code constraint that these are Blades...
    machine_id = Column(Integer,
                        ForeignKey('machine.machine_id',
                                   name='chassis_slot_machine_fk'),
                        nullable=True)
    #TODO: need a unique key against this, but what if it takes 2 slots?

    chassis = relation(Chassis, uselist=False,
                       backref=backref('slots', cascade='delete, delete-orphan',
                                       order_by=[asc('slot_number')]),
                       passive_deletes=True)

    machine = relation(Machine, uselist=False,
                       backref=backref('chassis_slot',
                                       cascade='delete, delete-orphan'))

chassis_slot = ChassisSlot.__table__
chassis_slot.primary_key.name = 'chassis_slot_pk'

table = chassis_slot


# We don't create any chassis anymore, so there's no point in this...

#def populate(sess, *args, **kw):
#
#    if len(sess.query(ChassisSlot).all()) < 1:
#        for c in sess.query(Chassis).all():
#            for node in range(1, 17):
#                a = ChassisSlot(chassis=c, slot_number=node)
#                sess.add(a)
#        sess.commit()
#        print 'created %d chassis slots' % sess.query(ChassisSlot).count()

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
