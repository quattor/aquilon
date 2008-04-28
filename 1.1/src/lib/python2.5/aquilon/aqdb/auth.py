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
from sqlalchemy import DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

realm = Table('realm', meta,
    Column('id', Integer, Sequence('realm_id_seq'), primary_key=True),
    Column('name', String(64), nullable=False),
    Column('creation_date', DateTime, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name',name='realm_uk'))
realm.create(checkfirst=True)

class Realm(aqdbBase):
    pass

mapper(Realm,realm,properties={
    'creation_date' : deferred(realm.c.creation_date),
    'comments'      : deferred(realm.c.comments)
})

user_principal = Table('user_principal', meta,
    Column('id', Integer, Sequence('user_principal_id_seq'), primary_key=True),
    Column('name', String(32), nullable=False),
    Column('realm_id', Integer, ForeignKey('realm.id'), nullable=False),
    Column('creation_date', DateTime,
           nullable=False, default=datetime.datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name','realm_id',name='user_principal_realm_uk'))
user_principal.create(checkfirst=True)

class UserPrincipal(aqdbBase):
    """ Simple class for strings representing users kerberos credential """
    def __init__(self,princ,**kw):
        if princ.isspace() or len(princ) < 1 :
            msg='Names must contain some non-whitespace characters'
            raise ArgumentError(msg)
        if isinstance(princ,str):
            self.name = princ.strip().lower()
        else:
            raise ArgumentError("Incorrect name argument %s" % princ)

        realm=kw.pop('realm','is1.morgan')
        if isinstance(realm,Realm):
            self.realm=realm
        else:
            rid=engine.execute(select([realm.c.id],realm.c.name==realm)).scalar()
            assert isinstance(rid,int), "Can't find realm '%s'"%realm
            self.realm_id=rid

    def __str__(self):
        return '@'.join([self.name,self.realm.name])
    def __repr__(self):
        return ' '.join([self.__class__.__name__,str(self)])

mapper(UserPrincipal,user_principal, properties={
    'realm'         : relation(Realm,uselist=False),
    'creation_date' : deferred(user_principal.c.creation_date),
    'comments'      : deferred(user_principal.c.comments)
})


if __name__ == '__main__':
    s = Session()
    if empty(realm):
        r=Realm('is1.morgan')
        s.save(r)
        s.commit()
        assert(r)
        s.close()

    if empty(user_principal):
        #i=user_principal.insert()
        r=s.query(Realm).first()
        assert(r.name == 'is1.morgan')

        for nm in ['njw', 'daqscott', 'wesleyhe', 'guyrol', 'quattor','cdb']:
            up=UserPrincipal(nm,realm=r)
            s.save(up)
            s.commit()
    print 'inserted some example user principals'

    a = s.query(UserPrincipal).first()
    assert(a)
