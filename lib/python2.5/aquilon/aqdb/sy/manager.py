#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" management interfaces as a subclass of System """

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

class Manager(System):
    __tablename__ = 'manager'

    id          = Column(Integer, ForeignKey(System.c.id, 
                                              ondelete = 'CASCADE', 
                                              name = 'mgr_system_fk'), 
                                             primary_key = True)

    machine_id  = Column(Integer, ForeignKey(Machine.c.id, 
                                               name = 'mgr_machine_fk'), 
                                              nullable = False)

    machine     = relation(Machine, uselist=False, backref='machine')

    __mapper_args__ = {'polymorphic_identity' : 'manager'}

manager = Manager.__table__
manager.primary_key.name = 'mgr_pk'

table = manager

def populate(db, *args, **kw):
    if len(db.s.query(Manager).all()) < 1:
        from aquilon.aqdb.net.dns_domain import DnsDomain
        nm = 'aquilon1-r'

        dom = db.s.query(DnsDomain).filter_by(name = 'one-nyp.ms.com').one()
        assert(dom)

        mgr = Manager(name=nm, dns_domain=dom)
        db.s.add(mgr)
        try:
            db.s.commit()
        except Exception, e:
            print e
            db.s.rollback()
            return False

    mgr = db.s.query(Manager).filter_by(name=nm).one()
    assert(mgr)
    assert(mgr.dns_domain)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
