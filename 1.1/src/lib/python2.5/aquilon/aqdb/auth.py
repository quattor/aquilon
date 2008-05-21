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
import os
sys.path.append('../..')


#from schema import (get_comment_col, get_date_col, get_id_col)
from db import *
#sys.path.append(
#    '/v/global/user/d/da/daqscott/Desktop/SQLAlchemy-0.4.6/lib')

from sqlalchemy import Table, Column, Integer, Sequence, String
from sqlalchemy import DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

class Role(Base):
    __table__ = Table('role', Base.metadata,
        Column('id', Integer, Sequence('roles_id_seq'),
               primary_key=True),
        Column('name', String(32), nullable=False),
        UniqueConstraint('name', name='role_name_uk'))

    comments = get_comment_col()
    creation_date = get_date_col()
#TODO: change this to full declarative, not with a table def
Role.__table__.create(checkfirst=True)

class Realm(Base):
    __table__ = Table('realm', meta,
    Column('id', Integer, Sequence('realm_id_seq'), primary_key=True),
    Column('name', String(64), nullable=False),
    UniqueConstraint('name',name='realm_uk'))

    comments = deferred(Column('comments',String(255),nullable=True))
    creation_date = deferred(
        Column('creation_date', DateTime, default=datetime.now))
Realm.__table__.create(checkfirst=True)

user_principal = Table('user_principal', meta,
    Column('id', Integer, Sequence('user_principal_id_seq'), primary_key=True),
    Column('name', String(32), nullable=False),
    Column('realm_id', Integer,
           ForeignKey('realm.id', name='usr_princ_rlm_fk'), nullable=False),
    Column('role_id', Integer,
           ForeignKey('role.id', name='usr_princ_role_fk'),
           nullable=False, default = id_getter(Role.__table__,
                                               Role.__table__.c.name,'nobody')),
    Column('creation_date', DateTime,
           nullable=False, default=datetime.now),
    Column('comments', String(255), nullable=True),
    UniqueConstraint('name','realm_id',name='user_principal_realm_uk'))
user_principal.create(checkfirst=True)

class UserPrincipal(aqdbBase):
    """ Simple class for strings representing users kerberos credential """
    @optional_comments
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
    'realm'         : relation(Realm, uselist=False),
    'role'          : relation(Role, uselist=False),
    'creation_date' : deferred(user_principal.c.creation_date),
    'comments'      : deferred(user_principal.c.comments)
})


if __name__ == '__main__':
    s = Session()
    #Base.metadata.create_all(checkfirst=True)
    #meta.create_all(checkfirst=True)


    if s.query(Realm).count() == 0:
        r=Realm(name='is1.morgan')
        s.save(r)
        s.commit()
        assert(r)
        print 'created %s'%(r)

    if s.query(Role).count() == 0:
        roles=['nobody','operations','engineering', 'aqd_admin']
        for i in roles:
            r=Role(name=i,comments='TEST')
            s.save(r)
            assert(r)
        s.commit()
        print 'created %s'%(roles)
    #Since .one() raises exceptions, they're in effect a nice assertion style
    #test that important roles are in place at module _run_ time.

    admin = s.query(Role).filter_by(name='aqd_admin').one()
    eng   = s.query(Role).filter_by(name='engineering').one()
    ops   = s.query(Role).filter_by(name='operations').one()

    #these are pulled from memory, so I'm sure I omitted a lot, but admins
    # can add anyone else into the frey.
    #TODO: sync from some ldap group ???

    admins  = ['cdb','njw', 'wesleyhe','guyroleh','daqscott',
               'kgreen', 'benjones']
    unixeng = ['cesarg','jasona', 'dankb','tonyc','goliaa','samsh','hagberg',
               'hookn', 'jelinker','kovasck','lookerm', 'bet','walkert','af',
               'lillied']
    unixops     = ['nathand','premdasr','bestc','chawlav','wbarnes']

    if empty(user_principal):
        r=s.query(Realm).first()
        assert(r.name == 'is1.morgan')

        for nm in admins:
            up=UserPrincipal(nm,realm=r,role=admin,comment='AutoPopulated')
            up.role=admin
            s.save(up)
            s.commit()
            assert(up)
        print 'created admins: %s'%(admins)

        for nm in unixeng:
            up=UserPrincipal(nm,realm=r,role=eng,comment='AutoPopulated')
            up.role=eng
            s.save(up)
            s.commit()
            assert(up)
        print 'created eng: %s'%(unixeng)

        for nm in unixops:
            up=UserPrincipal(nm,realm=r, role=ops, comment='AutoPopulated')
            up.role=ops
            s.save(up)
            s.commit()
            assert(up)
        print 'created eng: %s'%(ops)

        currentuser = os.environ.get('USER')
        if not s.query(UserPrincipal).filter_by(name=currentuser).first():
            up = UserPrincipal(currentuser, realm=r, role=admin)
            up.role=admin
            s.save(up)
            s.commit()
        print 'created ops: %s'%(ops)

    a = s.query(UserPrincipal).first()
    assert(a)
