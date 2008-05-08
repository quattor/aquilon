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

from db import *

from sqlalchemy import Table, Column, Integer, Sequence, String
from sqlalchemy import DateTime, UniqueConstraint, ForeignKey
from sqlalchemy.orm import mapper, relation, deferred

from roles import Role,Realm

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

    if empty(user_principal):
        r=s.query(Realm).first()
        assert(r.name == 'is1.morgan')

        userlist = ['njw', 'daqscott', 'wesleyhe', 'guyrol','cdb','jasona']
        for nm in userlist:
            up=UserPrincipal(nm,realm=r)
            s.save(up)
            s.commit()

        print 'inserted some example user principals'

        currentuser = os.environ.get('USER')
        if not currentuser in userlist:
            up = UserPrincipal(currentuser, realm=r)
            s.save(up)
            s.commit()

        adminrole = s.query(Role).filter_by(name='aqd_admin').one()
        dbuser = s.query(UserPrincipal).filter_by(
                name=currentuser, realm=r).one()
        dbuser.role = adminrole
        s.save_or_update(dbuser)
        s.commit()

        print 'made %s an admin' % dbuser.name

    a = s.query(UserPrincipal).first()
    assert(a)
