#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Represent secondary interfaces """

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.sy.system  import System
from aquilon.aqdb.hw.machine import Machine

class Auxiliary(System):
    __tablename__ = 'auxiliary'

    id = Column(Integer, ForeignKey('system.id',
                                     name = 'aux_system_fk',
                                     ondelete = 'CASCADE'),
                                    primary_key = True)

    machine_id  = Column(Integer, ForeignKey(Machine.c.id,
                                             name = 'aux_machine_fk'), 
                                            nullable = False)

    machine     = relation(Machine, uselist=False, backref='machine')
        
    __mapper_args__ = {'polymorphic_identity' : 'auxiliary'}

auxiliary = Auxiliary.__table__
auxiliary.primary_key.name = 'aux_pk'

table = auxiliary

def populate(db, *args, **kw):
    if len(db.s.query(Auxiliary).all()) < 1:
        from aquilon.aqdb.net.dns_domain import DnsDomain
        nm = 'aquilon1-e1'

        dom = db.s.query(DnsDomain).filter_by(name = 'one-nyp.ms.com').one()
        assert(dom)

        as=Auxiliary(name=nm, dns_domain=dom)
        db.s.add(qs)
        try:
            db.s.commit()
        except Exception, e:
            print e
            db.s.rollback()
            return False

    as=db.s.query(Auxiliary).filter_by(name=nm).one()
    assert(as)
    assert(as.dns_domain)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
