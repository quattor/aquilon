#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" At the moment,
    sublass of System """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

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

def populate(db, *args, **kw):
    if len(db.s.query(ConsoleServer).all()) < 1:
        from aquilon.aqdb.net.dns_domain import DnsDomain
        nm = 'test-cons-svr'

        #dom = db.s.query(DnsDomain).filter_by(name = 'one-nyp.ms.com').one()
        #assert(dom)

        # Requires ConsoleServerHw as a parameter
        #cs = ConsoleServer(name=nm, dns_domain=dom)
        #db.s.add(cs)
        #try:
            #db.s.commit()
        #except Exception, e:
            #print e
            #db.s.rollback()
            #return False

    #cs = db.s.query(ConsoleServer).filter_by(name=nm).one()
    #assert(cs)
    #assert(cs.dns_domain)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
