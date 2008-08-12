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


from datetime import datetime
import sys
import os

if __name__ == '__main__':
    DIR = os.path.dirname(os.path.realpath(__file__))
    sys.path.insert(0, os.path.realpath(os.path.join(DIR, '..', '..', '..')))
    import aquilon.aqdb.depends

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.db_factory import Base
from aquilon.aqdb.auth.role import Role, role
from aquilon.aqdb.auth.realm import Realm, realm


class UserPrincipal(Base):
    """ Simple class for strings representing users kerberos credential """
    __tablename__ = 'user_principal'
    id = Column(Integer, Sequence('user_principal_id_seq'), primary_key = True)
    name = Column(String(32), nullable = False)
    realm_id = Column(Integer, ForeignKey(
        'realm.id', name = 'usr_princ_rlm_fk'), nullable = False)

    role_id = Column(Integer, ForeignKey(
        'role.id', name='usr_princ_role_fk', ondelete = 'CASCADE'),
                     nullable = False)
                     #default = select(
                     #   [role.c.id]).where(
                     #   role.c.name=='nobody').execute().fetchone()[0])

    creation_date = deferred(Column(DateTime,
                                    nullable=False, default=datetime.now))
    comments = deferred(Column('comments', String(255), nullable=True))

    realm = relation(Realm, uselist = False)
    role  = relation(Role, uselist = False)

    def __str__(self):
        return '@'.join([self.name,self.realm.name])

user_principal = UserPrincipal.__table__
user_principal.primary_key.name = 'user_principal_pk'
user_principal.append_constraint(
    UniqueConstraint('name','realm_id',name='user_principal_realm_uk'))

def populate(*args, **kw):
    from aquilon.aqdb.db_factory import db_factory, Base
    from sqlalchemy import insert

    dbf = db_factory()
    Base.metadata.bind = dbf.engine
    if 'debug' in args:
        Base.metadata.bind.echo = True
    s = dbf.session()


    user_principal.create(checkfirst = True)

    admin = s.query(Role).filter_by(name = 'aqd_admin').one()
    eng   = s.query(Role).filter_by(name = 'engineering').one()
    ops   = s.query(Role).filter_by(name = 'operations').one()
    telco = s.query(Role).filter_by(name = 'telco_eng').one()

    admins  = ['cdb', 'njw', 'wesleyhe', 'guyroleh', 'daqscott', 'kgreen',
               'benjones']

    unixeng = ['cesarg', 'jasona', 'dankb', 'tonyc', 'goliaa', 'samsh',
               'hagberg', 'hookn', 'jelinker', 'kovacsk','lookerm', 'bet',
               'walkert', 'af', 'lillied']

    operations = ['nathand', 'premdasr', 'bestc', 'chawlav', 'wbarnes',
                  'gleasob', 'lchun', 'peteryip', 'richmoj', 'tipping',
                  'hardyb', 'martinva']

    telco_eng = ['dalys', 'medinad', 'peikonb', 'kulawiak']

    if len(s.query(UserPrincipal).all()) < 1:
        r = s.query(Realm).first()
        assert(r.name == 'is1.morgan')


        for nm in admins:
            up=UserPrincipal(name = nm, realm = r,role = admin,
                             comments = 'AutoPopulated')
            s.save(up)
            s.commit()
            assert(up)
        print 'created admins: %s'%(admins)

        for nm in unixeng:
            up=UserPrincipal(name = nm, realm = r,role = eng,
                             comments = 'AutoPopulated')
            s.save(up)
            s.commit()
            assert(up)
        print 'created eng: %s'%(unixeng)

        for nm in operations:
            up=UserPrincipal(name = nm, realm = r, role = ops,
                             comments = 'AutoPopulated')
            s.save(up)
            s.commit()
            assert(up)
        print 'created operations: %s'%(operations)

        for nm in telco_eng:
            up = UserPrincipal(name = nm, realm = r, role = telco,
                               comments = 'AutoPopulated')
            s.save(up)
            s.commit()
            assert(up)
        print 'created telco_eng: %s'%(telco_eng)

    a = s.query(UserPrincipal).first()
    assert(a)

    if Base.metadata.bind.echo == True:
        Base.metadata.bind.echo == False
