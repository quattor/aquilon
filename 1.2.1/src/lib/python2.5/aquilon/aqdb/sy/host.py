#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" For Systems and related objects """
from datetime import datetime

import sys
import os

DIR = os.path.dirname(os.path.realpath(__file__))
sys.path.insert(0,os.path.join(DIR, '..'))

import depends
from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from db_factory           import Base
from column_types.aqstr   import AqStr
from domain               import Domain
from cfg.archetype        import Archetype
from hw.machine           import Machine
from hw.status            import Status

class Host(Base):
    """ Here's our most common kind of System, the Host. Putting a physical
        machine into a chassis and powering it up leaves it in a state with a
        few more attributes not filled in: what Domain configures this host?
        What is the build/mcm 'status'? If Ownership is captured, this is the
        place for it. """

    __tablename__ = 'host'

    id = Column(Integer, ForeignKey(
        'system.id', ondelete = 'CASCADE', name = 'host_system_fk'),
                primary_key = True)

    machine_id   = Column(Integer, ForeignKey(
        'machine.id', name = 'host_machine_fk'), nullable = False)

    domain_id    = Column(Integer, ForeignKey(
        'domain.id', name = 'host_domain_fk'), nullable = False)

    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name = 'host_arch_fk'), nullable = False)

    status_id    = Column(Integer, ForeignKey(
        'status.id', name = 'host_status_fk'), nullable = False)

    machine   = relation(Machine,   backref = 'host', uselist = False)
    domain    = relation(Domain,    backref = 'hosts')
    archetype = relation(Archetype, backref = 'hosts')
    status    = relation(Status,    backref = 'hosts')

    """ The following relation is defined in BuildItem to avoid circular
    import dependencies. Perhaps it can be restated another way than
    to append the property onto Host there, left for future enhancement

    Host.templates = relation(BuildItem,
                         collection_class = ordering_list('position'),
                         order_by = [BuildItem.c.position]) """

    def _get_location(self):
        return self.machine.location
    location = property(_get_location) #TODO: make these synonms?

    def _sysloc(self):
        return self.machine.location.sysloc()
    sysloc = property(_sysloc)

    def __repr__(self):
        return 'Host %s'%(self.name)

#TODO: synonym for location, sysloc, fqdn (in system)
host = Host.__table__
host.primary_key.name = 'host_pk'
host.append_constraint(
    UniqueConstraint('name', 'domain_id', name = 'host_fqdn_uk'))


def populate():
    from db_factory import db_factory, Base
    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    Base.metadata.bind.echo = True
    s = dbf.session()

    host.create(checkfirst = True)
