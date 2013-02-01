# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Personality as a high level cfg object """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)
from sqlalchemy.sql import select
from sqlalchemy.orm import relation, deferred
from sqlalchemy.orm.session import object_session

from aquilon.aqdb.model import Base, Archetype
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'prsnlty'
_TN  = 'personality'

class Personality(Base):
    """ Personality names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    archetype_id = Column(Integer, ForeignKey(
        'archetype.id', name='%s_arch_fk'%(_ABV)), nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)
    comments = Column(String(255), nullable=True)

    archetype = relation(Archetype, backref='personality', uselist=False)

    def __repr__(self):
        s = ("<"+self.__class__.__name__ + " name ='"+ self.name +
             "', " + str(self.archetype) +'>')
        return s

    @classmethod
    def by_archetype(cls, dbarchetype):
        session = object_session(dbarchetype)
        return session.query(cls).filter(
            cls.__dict__['archetype'] == dbarchetype).all()


personality = Personality.__table__
table       = Personality.__table__


personality.primary_key.name='%s_pk'%(_ABV)
personality.append_constraint(UniqueConstraint('name', 'archetype_id',
                                               name='%s_uk'%(_TN)))

def populate(sess, *args, **kw):
    if len(sess.query(Personality).all()) > 0:
        return

    import os

    cfg_base = kw['cfg_base']
    assert os.path.isdir(cfg_base), "No such directory '%s'"%(cfg_base)

    for arch in sess.query(Archetype).all():
        #find aquilon archetype and all directories under it
        #change if we grow past having multiple archtypes w/ personalities
        if arch.name == 'aquilon':
            p = os.path.join(cfg_base, arch.name, 'personality')
            assert os.path.isdir(p), \
                    "Can't find personality directory '%s' in populate" % p
            for i in os.listdir(p):
                if os.path.isdir(os.path.abspath(os.path.join(p, i))):
                    pers = Personality(name=i, archetype=arch)
                    sess.add(pers)
        else:
            pers = Personality(name='generic', archetype=arch)
            sess.add(pers)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(Personality).first()
    assert(a)


