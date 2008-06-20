#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" If you can read this you should be documenting """
import depends
from datetime import datetime

import sqlalchemy
from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from db import Base
from machine import Machine, machine
from interface import Interface, interface

class SwitchPort(Base):
    __tablename__ = 'switch_port'

    switch_id   = Column(Integer,
                       ForeignKey('machine.id', ondelete='CASCADE',
                                  name = 'switch_mach_fk'), primary_key = True)
    #TODO: code level constraint on machine_type == tor_switch
    port_number  = Column(Integer, primary_key = True)
    interface_id = Column(Integer,
                          ForeignKey('interface.id', ondelete='CASCADE',
                                     name = 'switch_int_fk'), nullable = True)
    link_creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))
    #TODO: should this really go in another table?

    switch = relation(Machine, backref = 'switchport')
    interface = relation(Interface, backref = 'switchport')


switch_port = SwitchPort.__table__
switch_port.primary_key.name = 'switch_port_pk'
