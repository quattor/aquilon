""" The stores the hostname/mac/ip of specialized appliances for console service
    to machines and telco gear """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.sy.system import System
from aquilon.aqdb.hw.console_server_hw import ConsoleServerHw


class ConsoleServer(System):
    __tablename__ = 'console_server'

    id = Column(Integer,
                ForeignKey('system.id', ondelete = 'CASCADE',
                           name = 'cons_srv_system_fk'), primary_key = True)

    console_server_id = Column(Integer, ForeignKey(
        'console_server_hw.hardware_entity_id', name = 'cons_srv_sy_hw.fk',
        ondelete = 'CASCADE'), nullable = False)

    console_server_hw = relation(ConsoleServerHw, uselist=False,
                                 backref=backref('console_server',
                                                 cascade='delete'))

    __mapper_args__ = {'polymorphic_identity' : 'console_server'}

console_server = ConsoleServer.__table__
console_server.primary_key.name = 'cons_srv_pk'

table = console_server

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
