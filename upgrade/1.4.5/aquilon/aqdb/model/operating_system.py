# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2013  Contributor
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
""" Operating System as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.orm import relation
from sqlalchemy.orm.session import object_session

from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_TN  = 'operating_system'
_ABV = 'os'

class OperatingSystem(Base):
    """ Operating Systems """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    version = Column(AqStr(16), nullable=False )
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name='%s_arch_fk'%(_ABV)), nullable=False)
    #vendor id?
    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, backref='os', uselist=False)

    #cfg_path = os/name/version

    def __repr__(self):
        s = ("<"+self.__class__.__name__ + " "+ self.name +
             " " + self.version + " " + str(self.archetype) +'>')
        return s

    @classmethod
    def by_archetype(cls, dbarchetype):
        session = object_session(dbarchetype)
        return session.query(cls).filter(
            cls.__dict__['archetype'] == dbarchetype).all()


operating_system = OperatingSystem.__table__
table = operating_system

operating_system.primary_key.name = '%s_pk'% (_ABV)
operating_system.append_constraint(
    UniqueConstraint('name', 'version', 'archetype_id', name='%s_uk'% (_TN)))

def populate(sess, *args, **kw):
    if len(sess.query(OperatingSystem).all()) > 0:
        return

    aquilon = Archetype.get_by('name', 'aquilon', sess)[0]
    for ver in ['4.0.1-ia32', '4.0.1-x86_64', '5.0-x86_64']:
        os_obj = OperatingSystem(archetype=aquilon, name='linux', version=ver)
        sess.add(os_obj)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(OperatingSystem).first()
    assert a, "No operating system created by populate"
