# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
""" Configuration Branches for Systems """

from datetime import datetime

from sqlalchemy import (Table, Integer, Boolean, DateTime, Sequence, String,
                        Column, ForeignKey, UniqueConstraint,
                        ForeignKeyConstraint)
from sqlalchemy.orm import relation, backref

from aquilon.config import Config
from aquilon.utils import monkeypatch
from aquilon.aqdb.model import Base, UserPrincipal
from aquilon.aqdb.column_types.aqstr import AqStr


class Branch(Base):
    """
        Each branch of template-king represents a distinct set of
        templates in use broker-side (domains) or client-side (sandboxes)
        for testing and managing systems.
    """
    __tablename__ = 'branch'
    id = Column(Integer, Sequence('branch_id_seq'), primary_key=True)
    branch_type = Column(AqStr(16), nullable=False)
    name = Column(AqStr(32), nullable=False)

    compiler = Column(String(255), nullable=False)
    is_sync_valid = Column(Boolean, nullable=False, default=True)
    autosync = Column(Boolean, nullable=False, default=True)

    owner_id = Column(Integer, ForeignKey('user_principal.id',
                                          name='branch_user_princ_fk'),
                      nullable=False)

    creation_date = Column( DateTime, default=datetime.now, nullable=False)
    comments = Column('comments', String(255), nullable=True)

    owner = relation(UserPrincipal, uselist=False, backref='domain')

    __mapper_args__ = {'polymorphic_on': branch_type}

branch = Branch.__table__
branch.primary_key.name = 'branch_pk'
branch.append_constraint(UniqueConstraint('name', name='branch_uk'))

table = branch


class Domain(Branch):
    """
        Template branch where the checked out contents are managed
        solely by the broker.
    """
    __tablename__ = 'domain'

    domain_id = Column(Integer, ForeignKey('branch.id', name='domain_fk',
                                           ondelete='CASCADE'),
                       primary_key=True)

    tracked_branch_id = Column(Integer, ForeignKey('branch.id',
                                                   name='domain_branch_fk'),
                               nullable=True)
    rollback_commit = Column(AqStr(40), nullable=True)

    __mapper_args__ = {'polymorphic_identity': 'domain',
                       'inherit_condition': domain_id == Branch.id}

domain = Domain.__table__
domain.primary_key.name = 'domain_pk'
Domain.tracked_branch = relation(Branch, uselist=False, backref='trackers',
        primaryjoin=Domain.tracked_branch_id == Branch.id)


class Sandbox(Branch):
    """
        Template branch where the checked out contents are managed
        by a user.  Multiple users can have a sandbox checked out.
    """
    __tablename__ = 'sandbox'
    __mapper_args__ = {'polymorphic_identity': 'sandbox'}

    sandbox_id = Column(Integer, ForeignKey('branch.id', name='sandbox_fk',
                                            ondelete='CASCADE'),
                        primary_key=True)

sandbox = Sandbox.__table__
sandbox.primary_key.name = 'sandbox_pk'


@monkeypatch(domain)
def populate(sess, *args, **kw):
    if len(sess.query(Domain).all()) < 1:
        cdb = sess.query(UserPrincipal).filter_by(name='cdb').one()
        assert cdb, 'no cdb in populate domain'

        config = Config()
        compiler = config.get("panc", "pan_compiler")

        prod = Domain(name='prod', owner=cdb, tracked_branch=None,
                      compiler=compiler, comments='Production source domain.')
        sess.add(prod)
        sess.commit()

        ny = Domain(name='ny-prod', owner=cdb, tracked_branch=prod,
                    compiler=compiler,
                    comments='The NY regional production domain')
        sess.add(ny)
        sess.commit()

        d=sess.query(Domain).first()
        assert d, "No domains created by populate"
