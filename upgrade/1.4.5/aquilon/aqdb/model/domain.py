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
""" Configuration Domains for Systems """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref

from aquilon.aqdb.model import Base, UserPrincipal
from aquilon.aqdb.column_types.aqstr import AqStr


class Domain(Base):
    """
        Domain is to be used as the top most level for path traversal of
        the SCM. They represent individual configuration repositories.
    """
    __tablename__ = 'domain'
    id = Column(Integer, Sequence('domain_id_seq'), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    compiler = Column(String(255), nullable=False,
                      default='/ms/dist/elfms/PROJ/panc/8.2.3/bin/panc')

    owner_id = Column(Integer, ForeignKey('user_principal.id',
                                          name='domain_user_princ_fk'),
                      nullable=False)

    creation_date = Column( DateTime, default=datetime.now, nullable=False)
    comments = Column('comments', String(255), nullable=True)

    owner = relation(UserPrincipal, uselist=False, backref='domain')

domain = Domain.__table__
domain.primary_key.name='domain_pk'
domain.append_constraint(UniqueConstraint('name',name='domain_uk'))

table = domain

def populate(sess, *args, **kw):
    if len(sess.query(Domain).all()) < 1:
        cdb = sess.query(UserPrincipal).filter_by(name='cdb').one()
        assert(cdb)

        r = Domain(name='ny-prod', owner=cdb,
                   comments='The NY regional production domain')

        sess.add(r)
        sess.commit()

        d=sess.query(Domain).first()
        assert d, "No domains created by populate"
