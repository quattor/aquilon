#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" At the moment, quattor servers are exposed as a very dull
    sublass of System """


import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, select,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, deferred, backref

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.sy.system import System
from aquilon.aqdb.net.dns_domain import DnsDomain, dns_domain


class QuattorServer(System):
    __tablename__ = 'quattor_server'

    id = Column(Integer,
                ForeignKey('system.id', ondelete = 'CASCADE',
                           name = 'qs_system_fk'), primary_key = True)

    system = relation(System, uselist = False, backref = 'quattor_server')
    __mapper_args__ = {'polymorphic_identity' : 'quattor_server'}

quattor_server = QuattorServer.__table__
quattor_server.primary_key.name = 'qs_pk'

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()

    quattor_server.create(checkfirst = True)

    if len(s.query(QuattorServer).all()) < 1:
        dom = s.query(DnsDomain).filter_by(name = 'ms.com').one()
        qs=QuattorServer(name='oziyp2', dns_domain=dom)
        s.add(qs)
        s.commit()

    qs=s.query(QuattorServer).filter_by(name='oziyp2').one()
    assert(qs)
    assert(qs.dns_domain)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
