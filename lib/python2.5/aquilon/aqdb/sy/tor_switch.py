#!/ms/dist/python/PROJ/core/2.5.0/bin/python
""" Comment me"""

import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import Integer, Column, ForeignKey
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.sy.system        import System
from aquilon.aqdb.hw.tor_switch_hw import TorSwitchHw

class TorSwitch(System):
    __tablename__ = 'tor_switch'

    id = Column(Integer,
                ForeignKey('system.id', ondelete = 'CASCADE',
                           name = 'tor_sw_sys_fk'), primary_key = True)

    tor_switch_id = Column(Integer, ForeignKey('tor_switch_hw.hardware_entity_id',
                                               name = 'tor_sw_sy_hw.fk',
                                               ondelete = 'CASCADE'),
                                              nullable = False)

    #system        = relation(System, uselist=False, backref='tor_switch')
    tor_switch_hw = relation(TorSwitchHw, uselist=False,
                             backref=backref('tor_switch',cascade='delete'))

    __mapper_args__ = {'polymorphic_identity' : 'tor_switch'}

tor_switch = TorSwitch.__table__
tor_switch.primary_key.name = 'tor_switch_pk'

table = tor_switch

#def populate(db, *args, **kw):
    #if len(db.s.query(TorSwitch).all()) < 1:

        #qs=TorSwitch(name='oziyp2', dns_domain=dom)
        #db.s.add(qs)
        #try:
        #    db.s.commit()
        #except Exception, e:
        #    print e
        #    db.s.rollback()
        #    return False

    #qs=db.s.query(TorSwitch).filter_by(name='oziyp2').one()
    #assert(qs)

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
