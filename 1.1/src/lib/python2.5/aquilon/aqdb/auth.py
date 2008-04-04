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
from __future__ import with_statement
import datetime
import sys
sys.path.append('../..')

from db import *

from sqlalchemy import Table, Column, Integer, Sequence, String
from sqlalchemy import ForeignKey, DateTime
from sqlalchemy.orm import mapper, relation, deferred

user_principle = Table('user_principle', meta,
    Column('id', Integer, Sequence('user_principle_id_seq'), primary_key=True),
    Column('name', String(32), unique=True, index=True, nullable=False),
    Column('creation_date', DateTime,
           nullable=False, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True))
user_principle.create(checkfirst=True)

class UserPrinciple(aqdbBase):
    """ Simple class for strings representing users kerberos credential """
    pass

mapper(UserPrinciple,user_principle, properties={
    'creation_date' : deferred(user_principle.c.creation_date),
    'comments': deferred(user_principle.c.comments)
})

if __name__ == '__main__':
    if empty(user_principle):
        i=user_principle.insert()
        for nm in ['njw','daqscott','wesleyhe','guyrol']:
            i.execute(name=nm)
    print 'inserted some example user principles'

    a=Session.query(UserPrinciple).first()
    assert(a)
