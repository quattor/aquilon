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
""" The module governing tables and objects that represent IP networks in
    Aquilon."""

#TODO: nullable location id.
#TODO: nullable description column?
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, Location
from aquilon.aqdb.column_types.aqstr import AqStr


_TN = 'dns_domain'

class DnsDomain(Base):
    """ For Dns Domain names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    def __str__(self):
        return str(self.name)


dns_domain = DnsDomain.__table__
table = DnsDomain.__table__


dns_domain.primary_key.name='%s_pk'%(_TN)
dns_domain.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))

def populate(sess, *args, **kw):

    if len(sess.query(DnsDomain).all()) < 1:

        ms   = DnsDomain(name='ms.com')#,
                         #audit_info = kw['audit_info'])

        onyp = DnsDomain(name='one-nyp.ms.com',
                         #audit_info = kw['audit_info'])
                         comments = '1 NYP test domain')

        devin1 = DnsDomain(name='devin1.ms.com',
                           #audit_info = kw['audit_info'])
                           comments='43881 Devin Shafron Drive domain')

        theha = DnsDomain(name='the-ha.ms.com',
                          #audit_info = kw['audit_info'])
                          comments='HA domain')

        for i in (ms, onyp, devin1, theha):
            sess.add(i)

        try:
            sess.commit()
        except Exception, e:
            sess.rollback()
            raise e


