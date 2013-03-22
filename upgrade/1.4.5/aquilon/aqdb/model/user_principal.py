# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
""" Contains tables and objects for authorization in Aquilon """

from datetime import datetime

from sqlalchemy import (Table, Column, Integer, DateTime, Sequence, String,
                        select, ForeignKey, PassiveDefault, UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Role, Realm


class UserPrincipal(Base):
    """ Simple class for strings representing users kerberos credential """
    __tablename__ = 'user_principal'

    id = Column(Integer, Sequence('user_principal_id_seq'), primary_key=True)

    name = Column(String(32), nullable=False)

    realm_id = Column(Integer, ForeignKey(
        'realm.id', name='usr_princ_rlm_fk'), nullable=False)

    role_id = Column(Integer, ForeignKey(
        'role.id', name='usr_princ_role_fk', ondelete='CASCADE'),
                     nullable=False)

    creation_date = deferred(Column(DateTime,
                                    nullable=False, default=datetime.now))

    comments = deferred(Column('comments', String(255), nullable=True))

    realm = relation(Realm, uselist=False)
    role  = relation(Role, uselist=False)

    def __str__(self):
        return '@'.join([self.name,self.realm.name])

user_principal = UserPrincipal.__table__
user_principal.primary_key.name='user_principal_pk'
user_principal.append_constraint(
    UniqueConstraint('name','realm_id',name='user_principal_realm_uk'))

table = user_principal

def populate(sess, *args, **kw):
    if len(sess.query(UserPrincipal).all()) < 1:
        log = kw['log']
        from sqlalchemy import insert

        admin = sess.query(Role).filter_by(name='aqd_admin').one()
        eng   = sess.query(Role).filter_by(name='engineering').one()
        ops   = sess.query(Role).filter_by(name='operations').one()
        telco = sess.query(Role).filter_by(name='telco_eng').one()

        admins  = ['cdb', 'aqdqa', 'njw', 'wesleyhe', 'daqscott', 'kgreen',
                   'benjones']

        unixeng = ['cesarg', 'jasona', 'dankb', 'goliaa', 'samsh', 'hagberg',
                   'hookn', 'jelinker', 'kovacsk', 'lookerm', 'walkert', 'af',
                   'lillied']

        operations = ['premdasr', 'bestc', 'chawlav', 'wbarnes', 'gleasob',
                      'lchun', 'peteryip', 'richmoj', 'hardyb', 'martinva']

        telco_eng = ['dalys', 'medinad', 'peikonb', 'kulawiak']

        r = sess.query(Realm).first()
        assert(r.name == 'is1.morgan')

        for nm in admins:
            up=UserPrincipal(name = nm, realm = r,role = admin,
                             comments = 'AutoPopulated')
            sess.add(up)
            sess.commit()
            assert(up)

        for nm in unixeng:
            up=UserPrincipal(name = nm, realm = r,role = eng,
                             comments = 'AutoPopulated')
            sess.add(up)
            sess.commit()
            assert(up)

        for nm in operations:
            up=UserPrincipal(name = nm, realm = r, role = ops,
                             comments = 'AutoPopulated')
            sess.add(up)
            sess.commit()
            assert(up)

        for nm in telco_eng:
            up = UserPrincipal(name = nm, realm = r, role = telco,
                               comments = 'AutoPopulated')
            sess.add(up)
            sess.commit()
            assert(up)

        cnt = len(sess.query(UserPrincipal).all())
        assert(cnt > 0)
        log.debug('created %s users'%(cnt))
