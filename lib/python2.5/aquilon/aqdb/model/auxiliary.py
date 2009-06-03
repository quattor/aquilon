""" Represent secondary interfaces """

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation

from aquilon.aqdb.model import System, Machine

class Auxiliary(System):
    __tablename__ = 'auxiliary'

    id = Column(Integer, ForeignKey('system.id',
                                    name='aux_system_fk',
                                    ondelete='CASCADE'),
                primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                             name='aux_machine_fk'),
                         nullable=False)

    machine = relation(Machine, backref='auxiliaries')

    __mapper_args__ = {'polymorphic_identity':'auxiliary'}

auxiliary = Auxiliary.__table__
auxiliary.primary_key.name='aux_pk'

table = auxiliary

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
