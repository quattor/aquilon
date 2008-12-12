""" management interfaces as a subclass of System """

from sqlalchemy import (Integer, String, Column, ForeignKey)
from sqlalchemy.orm import relation

from aquilon.aqdb.sy.system  import System
from aquilon.aqdb.hw.machine import Machine

class Manager(System):
    __tablename__ = 'manager'

    id          = Column(Integer, ForeignKey('system.id',
                                              ondelete = 'CASCADE',
                                              name = 'mgr_system_fk'),
                                             primary_key = True)

    machine_id  = Column(Integer, ForeignKey('machine.machine_id',
                                               name = 'mgr_machine_fk'),
                                              nullable = False)

    machine     = relation(Machine, uselist=False, backref='manager')

    __mapper_args__ = {'polymorphic_identity' : 'manager'}

manager = Manager.__table__
manager.primary_key.name = 'mgr_pk'

table = manager

#def populate(db, *args, **kw):
#    s = db.Session()
#
#    if len(s.query(Manager).all()) < 1:
#        from aquilon.aqdb.net.dns_domain import DnsDomain
#        nm = 'aquilon1-r'
#
#        dom = s.query(DnsDomain).filter_by(name = 'one-nyp.ms.com').one()
#        assert(dom)
#
#        mgr = Manager(name=nm, dns_domain=dom)
#        s.add(mgr)
#
#        try:
#            s.commit()
#        except Exception, e:
#            #FIX ME: need to create a machine, interface, and host to test this
#            print e
#            s.close()
#            return False
#
#    mgr = s.query(Manager).filter_by(name=nm).one()
#    assert(mgr)
#    assert(mgr.dns_domain)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
