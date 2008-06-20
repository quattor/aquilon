#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
""" Contains tables and objects for authorization in Aquilon """
import datetime
import sys
import os
sys.path.insert(0,'../')

from db import *

from sqlalchemy import Table, Column, Integer, Sequence, String
from sqlalchemy import DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

class Role(Base):
    __table__ = Table('role', Base.metadata,
        Column('id', Integer, Sequence('role_id_seq'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        UniqueConstraint('name', name='role_name_uk'))

    #comments = get_comment_col()
    #creation_date = get_date_col()
#TODO: change this to full declarative, not with a table def
Role.comments = Column('comments', String(255), nullable=True)
Role.creation_date = Column('creation_date', DateTime, default=datetime.now)
Role.__table__.create(checkfirst=True)

def populate_role():
    if s.query(Role).count() == 0:
        roles=['nobody','operations','engineering', 'aqd_admin']
        for i in roles:
            r=Role(name=i,comments='TEST')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)
