""" The majority of the things we're interested in for now are hosts. """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import (Base, System, Domain, Machine, Status,
                                Personality)
from aquilon.aqdb.column_types.aqstr import AqStr


class Host(System):
    """ Here's our most common kind of System, the Host. Putting a physical
        machine into a chassis and powering it up leaves it in a state with a
        few more attributes not filled in: what Domain configures this host?
        What is the build/mcm 'status'? If Ownership is captured, this is the
        place for it. """

    __tablename__ = 'host'
    __mapper_args__ = {'polymorphic_identity':'host'}

    id = Column(Integer, ForeignKey('system.id',
                                    ondelete='CASCADE',
                                    name='host_system_fk'),
                primary_key=True)

    machine_id = Column(Integer, ForeignKey('machine.machine_id',
                                            name='host_machine_fk'),
                        nullable=False)

    domain_id = Column(Integer, ForeignKey('domain.id',
                                           name='host_domain_fk'),
                       nullable=False)

    personality_id = Column(Integer, ForeignKey('personality.id',
                                                name='host_prsnlty_fk'),
                            nullable=False)

    status_id = Column(Integer, ForeignKey('status.id',
                                              name='host_status_fk'),
                          nullable=False)

    machine = relation(Machine, backref=backref('host', uselist=False))
    domain = relation(Domain, backref='hosts')
    personality = relation(Personality, backref='hosts')
    status = relation(Status, backref='hosts')

    """ The following relation is defined in BuildItem to avoid circular
    import dependencies. Perhaps it can be restated another way than
    to append the property onto Host there, left for future enhancement

    Host.templates = relation(BuildItem,
                         collection_class = ordering_list('position'),
                         order_by = [BuildItem.__table__.c.position]) """

    def _get_location(self):
        return self.machine.location
    location = property(_get_location) #TODO: make these synonms?

    def _get_sysloc(self):
        return self.machine.location.sysloc()
    sysloc = property(_get_sysloc)

    def _get_archetype(self):
        return self.personality.archetype
    archetype = property(_get_archetype)

    def __repr__(self):
        return 'Host %s'%(self.name)

#TODO: synonym for location, sysloc, fqdn (in system)
host = Host.__table__
host.primary_key.name='host_pk'
host.append_constraint(
    UniqueConstraint('machine_id', 'domain_id', name='host_machine_domain_uk'))

table = host

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
