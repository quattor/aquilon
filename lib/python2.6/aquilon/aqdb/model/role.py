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
""" Contains tables and objects for authorization in Aquilon """
from datetime import datetime

from sqlalchemy import (Column, Integer, String, DateTime, Sequence,
                        UniqueConstraint)

from aquilon.aqdb.model import Base
from aquilon.utils import monkeypatch
from aquilon.aqdb.column_types.aqstr import AqStr

roles = ['nobody', 'operations', 'engineering', 'aqd_admin', 'telco_eng',
         'maintech', 'unixops_l2']

#Upfront Design Decisions:
#  -Needs it's own creation_date + comments columns. Audit log depends on
#   this table for it's info, and would have a circular dependency


class Role(Base):
    __tablename__ = 'role'

    id = Column(Integer, Sequence('role_id_seq'), primary_key=True)

    name = Column(AqStr(32), nullable=False)

    creation_date = Column(DateTime, nullable=False, default=datetime.now)

    comments = Column('comments', String(255), nullable=True)

role = Role.__table__

role.primary_key.name = 'role_pk'
role.append_constraint(UniqueConstraint('name', name='role_uk'))
role.info['unique_fields'] = ['name']


@monkeypatch(role)
def populate(sess, **kw):
    """ populate our roles """
    if sess.query(Role).count() >= len(roles):
        return

    for i in roles:
        r = Role(name=i)
        sess.add(r)

    try:
        sess.commit()
    except Exception, e:
        sess.rollback()
        raise e
