""" Contains tables and objects for authorization in Aquilon """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Role, Realm


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

table = user_principal

def populate(sess, *args, **kw):
    if len(sess.query(UserPrincipal).all()) < 1:
        log = kw['log']
        from sqlalchemy import insert

        admin = sess.query(Role).filter_by(name = 'aqd_admin').one()
        eng   = sess.query(Role).filter_by(name = 'engineering').one()
        ops   = sess.query(Role).filter_by(name = 'operations').one()
        telco = sess.query(Role).filter_by(name = 'telco_eng').one()

        admins  = ['cdb', 'njw', 'wesleyhe', 'daqscott', 'kgreen', 'benjones']

        unixeng = ['cesarg', 'jasona', 'dankb', 'tonyc', 'goliaa', 'samsh',
                   'hagberg', 'hookn', 'jelinker', 'kovacsk','lookerm', 'bet',
                    'walkert', 'af', 'lillied']

        operations = ['nathand', 'premdasr', 'bestc', 'chawlav', 'wbarnes',
                      'gleasob', 'lchun', 'peteryip', 'richmoj', 'hardyb',
                      'martinva', 'andersme']

        telco_eng = ['dalys', 'medinad', 'peikonb', 'kulawiak']

        r = sess.query(Realm).first()
        assert(r.name == 'is1.morgan')

        for nm in admins:
            up=UserPrincipal(name = nm, realm = r,role = admin,
                             comments = 'AutoPopulated')
            sess.save(up)
            sess.commit()
            assert(up)

        for nm in unixeng:
            up=UserPrincipal(name = nm, realm = r,role = eng,
                             comments = 'AutoPopulated')
            sess.save(up)
            sess.commit()
            assert(up)

        for nm in operations:
            up=UserPrincipal(name = nm, realm = r, role = ops,
                             comments = 'AutoPopulated')
            sess.save(up)
            sess.commit()
            assert(up)

        for nm in telco_eng:
            up = UserPrincipal(name = nm, realm = r, role = telco,
                               comments = 'AutoPopulated')
            sess.save(up)
            sess.commit()
            assert(up)

        cnt = len(sess.query(UserPrincipal).all())
        assert(cnt > 0)
        log.debug('created %s users'%(cnt))

# Copyright (C) 2008 Morgan Stanley
# This module is part of Aquilon

# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
