#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Switch Ports model the ports of switches and are they physical connections
    to other machines' physical interfaces via the foreign key to interface """


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.db_factory    import Base
from aquilon.aqdb.hw.machine    import Machine
from aquilon.aqdb.hw.interface  import Interface


class SwitchPort(Base):
    """ Tor switches are types of machines (for now at least). What they
        have, besides their own interfaces and a network they provide, are
        ports, which connect to physical interfaces (but we'll use interface)
        ID in case we may want to bind in other interfaces later). """
    __tablename__ = 'switch_port'

    #TODO: code level constraint on machine_type == tor_switch
    switch_id   = Column(Integer,
                       ForeignKey('machine.id', ondelete='CASCADE',
                                  name = 'switch_mach_fk'), primary_key = True)

    port_number  = Column(Integer, primary_key = True)
    interface_id = Column(Integer,
                          ForeignKey('interface.id', ondelete='CASCADE',
                                     name = 'switch_int_fk'), nullable = True)
    link_creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))

    switch    = relation(Machine,   uselist = False, backref = 'switchport')
    interface = relation(Interface, uselist = False, backref = 'switchport')
    #TODO: another relation specified by interface type?

switch_port = SwitchPort.__table__
switch_port.primary_key.name = 'switch_port_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    switch_port.create(checkfirst = True)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
