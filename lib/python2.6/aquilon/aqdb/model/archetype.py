# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
""" Archetype specifies the metaclass of the build """
from datetime import datetime
from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint, Boolean)
from sqlalchemy.orm import relation, deferred

from aquilon.aqdb.model import Base
from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types.aqstr import AqStr

_ABV = 'archetype'

_archetypes = ['aquilon', 'windows', 'aurora', 'aegis', 'vmhost', 'pserver']
_compileable = ['aquilon', 'vmhost', 'pserver']


class Archetype(Base):
    """ Archetype names """
    __tablename__  = _ABV

    id = Column(Integer, Sequence('%s_id_seq'%(_ABV)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    is_compileable = Column(Boolean, default=False, nullable=False)
    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))
    comments = deferred(Column(String(255), nullable=True))

archetype = Archetype.__table__
table = Archetype.__table__

archetype.primary_key.name='%s_pk'%(_ABV)
archetype.append_constraint(UniqueConstraint('name',name='%s_uk'%(_ABV)))


@monkeypatch(archetype)
def populate(sess, *args, **kw):
    if len(sess.query(Archetype).all()) > 0:
        return

    for a_name in _archetypes:
        a = Archetype(name=a_name)
        if a_name in _compileable:
            a.is_compileable = True

        sess.add(a)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e

    a = sess.query(Archetype).first()
    assert(a)
