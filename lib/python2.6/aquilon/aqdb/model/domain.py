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
""" Configuration Domains for Systems """

from datetime import datetime

from sqlalchemy import (Table, Integer, DateTime, Sequence, String, Column,
                        ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation, backref

from aquilon.utils import monkeypatch
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


@monkeypatch(domain)
def populate(sess, *args, **kw):
    if len(sess.query(Domain).all()) < 1:
        cdb = sess.query(UserPrincipal).filter_by(name='cdb').one()
        assert cdb, 'no cdb in populate domain'

        r = Domain(name='ny-prod', owner=cdb,
                   comments='The NY regional production domain')

        sess.add(r)
        sess.commit()

        d=sess.query(Domain).first()
        assert d, "No domains created by populate"
