# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
""" Status is an overloaded term, but we use it to represent various stages of
    deployment, such as production, QA, dev, etc. each of which are also
    overloaded terms... """
from datetime import datetime

from sqlalchemy import (Column, Integer, DateTime, Sequence, String, ForeignKey,
                        UniqueConstraint)

from aquilon.aqdb.model import Base
from aquilon.aqdb.column_types.aqstr import AqStr

_statuses = ['blind', 'build', 'ready']

_TN = 'status'

class Status(Base):
    """ Status names """
    __tablename__  = _TN

    id = Column(Integer, Sequence('%s_id_seq'%(_TN)), primary_key=True)
    name = Column(AqStr(32), nullable=False)
    creation_date = Column(DateTime, default=datetime.now,
                                    nullable=False )
    comments = Column(String(255), nullable=True)

    def __init__(self,name):
        e = "Status is a static table and can't be instanced, only queried."
        raise ValueError(e)

    def __repr__(self):
        return str(self.name)

status = Status.__table__
table  = Status.__table__

status.primary_key.name='%s_pk'%(_TN)
status.append_constraint(UniqueConstraint('name',name='%s_uk'%(_TN)))


def populate(sess, *args, **kw):
    from sqlalchemy import insert
    from sqlalchemy.exceptions import IntegrityError

    if len(sess.query(Status).all()) < len(_statuses):
        i=status.insert()
        for name in _statuses:
            try:
                i.execute(name=name)
            except IntegrityError:
                pass

    assert len(sess.query(Status).all()) == len(_statuses)


