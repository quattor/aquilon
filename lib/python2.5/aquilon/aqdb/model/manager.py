""" management interfaces as a subclass of System """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Machine, System

class Manager(System):
    __tablename__ = 'manager'

    id = Column(Integer, ForeignKey('system.id',
                                    name='mgr_system_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='mgr_machine_fk'),
                        nullable=False)

    machine = relation(Machine, uselist=False, backref='manager')

    __mapper_args__ = {'polymorphic_identity':'manager'}

manager = Manager.__table__
manager.primary_key.name = 'mgr_pk'

table = manager

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
