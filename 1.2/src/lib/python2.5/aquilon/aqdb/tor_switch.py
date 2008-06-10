#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Top of Rack (TOR) Switches sit inside grid racks and provide connectivity
    to the core network. They have unique properties which allow us to have
    insight into the network access path of the hosts living the rack """

from __future__ import with_statement
import datetime
import sys
import os

if __name__ == '__main__':
    sys.path.append('../..')

from db import *
from location import Location
from systemType import SystemType, get_sys_type_id
from network import DnsDomain
from systems import System

from sqlalchemy     import (Table, Column, Integer, String, DateTime, Sequence,
                            UniqueConstraint, PrimaryKeyConstraint, ForeignKey)
from sqlalchemy.orm import mapper, relation, deferred

class TorSwitch(Base, System):
    __table__  = Table('tor_switch', Base.metadata,
        Column('id', Integer,
               ForeignKey('system.id', name='tor_switch_system_fk',
               ondelete='CASCADE'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        Column('dns_domain_id', Integer,
               ForeignKey('dns_domain.id', name='tor_switch_dns_domain_fk'),
               nullable=False),
        Column('system_type_id', Integer,
               ForeignKey('system_type.id', name='tor_switch_system_type_fk'),
               nullable=False),
        Column('location_id', Integer,
               ForeignKey('location.id', name='tor_switch_location_fk'),
               nullable=False),
        UniqueConstraint('name', name='tor_switch_name_uk'),
        PrimaryKeyConstraint('id', name = 'tor_switch_pk'))

    system      = relation(System, uselist=False, backref='tor_switch')
    dns_domain  = relation(DnsDomain)
    system_type = relation(SystemType)
    location    = relation(Location)

    __mapper_args__ = {'polymorphic_identity': get_sys_type_id('tor_switch'),
            'inherits': System}

    #comments = get_comment_col()
    #creation_date = get_date_col()
#TODO: change this to full declarative, not with a table def
TorSwitch.comments = Column('comments', String(255), nullable=True)
TorSwitch.creation_date = Column('creation_date',
                                 DateTime, default=datetime.now)

tor_switch = TorSwitch.__table__

tor_switch.create(checkfirst=True)
