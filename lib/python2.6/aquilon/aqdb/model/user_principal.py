# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base, Role, Realm


class UserPrincipal(Base):
    """ Simple class for strings representing users kerberos credential """
    __tablename__ = 'user_principal'

    id = Column(Integer, Sequence('user_principal_id_seq'), primary_key=True)

    name = Column(String(32), nullable=False)

    realm_id = Column(Integer, ForeignKey('realm.id', name='usr_princ_rlm_fk'),
                      nullable=False)

    role_id = Column(Integer, ForeignKey('role.id', name='usr_princ_role_fk',
                                         ondelete='CASCADE'),
                     nullable=False)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    role = relation(Role, innerjoin=True)
    realm = relation(Realm, innerjoin=True)

    __table_args__ = (UniqueConstraint(name, realm_id,
                                       name='user_principal_realm_uk'),)

    def __str__(self):
        return '@'.join([self.name, self.realm.name])

user_principal = UserPrincipal.__table__  # pylint: disable=C0103
user_principal.primary_key.name = 'user_principal_pk'
user_principal.info['unique_fields'] = ['name', 'realm']
