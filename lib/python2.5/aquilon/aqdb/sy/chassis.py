#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Comment Me"""

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy                  import Integer, Column, ForeignKey
from sqlalchemy.orm              import relation

from aquilon.aqdb.sy.system      import System
from aquilon.aqdb.hw.chassis_hw  import ChassisHw

class Chassis(System):
    __tablename__ = 'chassis'

    id              = Column(Integer, ForeignKey(System.c.id, 
                                    name = 'chassis_sys_fk',
                                    ondelete = 'CASCADE'),
                                   primary_key = True)

    chassis_hw_id   = Column(Integer, ForeignKey(ChassisHw.c.id, 
                                               name = 'chassis_sys_hw_fk', 
                                               ondelete='CASCADE'), 
                                              nullable=False)
                
    system          = relation(System, uselist=False, backref='chassis')
    chassis_hw      = relation(ChassisHw, uselist=False, backref='chassis')
    
    __mapper_args__ = {'polymorphic_identity' : 'chassis'}

chassis = Chassis.__table__
chassis.primary_key.name = 'chassis_pk'

table = chassis

#def populate(db, *args, **kw):
    #if len(db.s.query(Chassis).all()) < 1:

        #qs=Chassis(name='oziyp2', dns_domain=dom)
        #db.s.add(qs)
        #try:
        #    db.s.commit()
        #except Exception, e:
        #    print e
        #    db.s.rollback()
        #    return False

    #qs=db.s.query(Chassis).filter_by(name='oziyp2').one()
    #assert(qs)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
