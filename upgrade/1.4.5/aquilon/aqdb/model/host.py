# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" The majority of the things we're interested in for now are hosts. """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.model import (Base, System, Domain, Machine, Status,
                                Personality, OperatingSystem)
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

    operating_system_id = Column(Integer, ForeignKey('operating_system.id',
                                                     name='host_os_fk'),
                                 nullable=False)

    machine = relation(Machine, backref=backref('host', uselist=False))
    domain = relation(Domain, backref='hosts')
    personality = relation(Personality, backref='hosts')
    status = relation(Status, backref='hosts')
    operating_system = relation(OperatingSystem, uselist=False, backref='hosts')

    """ The following relation is defined in BuildItem to avoid circular
    import dependencies. Perhaps it can be restated another way than
    to append the property onto Host there, left for future enhancement

    Host.templates = relation(BuildItem,
                         collection_class = ordering_list('position'),
                         order_by = [BuildItem.__table__.c.position]) """

    #TODO: make thse synonyms?
    @property
    def location(self):
        return self.machine.location

    @property
    def sysloc(self):
        return self.machine.location.sysloc()

    @property
    def archetype(self):
        return self.personality.archetype

    def __repr__(self):
        return 'Host %s'%(self.name)

#TODO: synonym for location, sysloc, fqdn (in system)
host = Host.__table__
host.primary_key.name='host_pk'
host.append_constraint(
    UniqueConstraint('machine_id', 'domain_id', name='host_machine_domain_uk'))

table = host
