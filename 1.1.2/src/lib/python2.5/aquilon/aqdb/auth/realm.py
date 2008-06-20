#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" If you can read this you should be documenting """
import datetime
import sys
import os
sys.path.insert(0,'..')

from db import *

from sqlalchemy import (Table, Column, Integer, Sequence, String, DateTime,
                        UniqueConstraint, ForeignKey )
from sqlalchemy.orm import mapper, relation, deferred

class Realm(Base):
    __table__ = Table('realm', meta,
    Column('id', Integer, Sequence('realm_id_seq'), primary_key=True),
    Column('name', String(64), nullable=False),
    UniqueConstraint('name',name='realm_uk'))

    comments = deferred(Column('comments',String(255),nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))
#Realm.comments = Column('comments', String(255), nullable=True)
#Realm.creation_date = Column('creation_date', DateTime, default=datetime.now)
#make_name
realm = Realm.__table__

def populate_realm():
    if s.query(Realm).count() == 0:
        r=Realm(name='is1.morgan')
        s.save(r)
        s.commit()
        assert(r)
        print 'created %s'%(r)
