# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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

from sqlalchemy import (Integer, Boolean, DateTime, Sequence, String,
                        Column, ForeignKey, UniqueConstraint)
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Base, UserPrincipal
from aquilon.aqdb.column_types.aqstr import AqStr

_TN = "branch"
_DMN = "domain"
_SBX = "sandbox"


class Branch(Base):
    """
        Each branch of template-king represents a distinct set of
        templates in use broker-side (domains) or client-side (sandboxes)
        for testing and managing systems.
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    branch_type = Column(AqStr(16), nullable=False)

    name = Column(AqStr(32), nullable=False)

    compiler = Column(String(255), nullable=False)

    is_sync_valid = Column(Boolean(name="%s_is_sync_valid_ck" % _TN),
                           nullable=False, default=True)

    autosync = Column(Boolean(name="%s_autosync_ck" % _TN), nullable=False,
                      default=True)

    owner_id = Column(Integer, ForeignKey('user_principal.id',
                                          name='%s_user_princ_fk' % _TN),
                      nullable=False)

    creation_date = Column(DateTime, default=datetime.now, nullable=False)

    comments = Column(String(255), nullable=True)

    owner = relation(UserPrincipal, uselist=False, backref='domain')

    __mapper_args__ = {'polymorphic_on': branch_type}

branch = Branch.__table__  # pylint: disable=C0103, E1101
branch.primary_key.name = '%s_pk' % _TN
branch.append_constraint(UniqueConstraint('name', name='%s_uk' % _TN))
branch.info['unique_fields'] = ['name']


class Domain(Branch):
    """
        Template branch where the checked out contents are managed
        solely by the broker.
    """
    __tablename__ = _DMN

    domain_id = Column(Integer, ForeignKey('branch.id', name='%s_fk' % _DMN,
                                           ondelete='CASCADE'),
                       primary_key=True)

    tracked_branch_id = Column(Integer, ForeignKey('branch.id',
                                                   name='%s_branch_fk' % _DMN),
                               nullable=True)
    rollback_commit = Column(AqStr(40), nullable=True)

    requires_change_manager = Column(Boolean(name="%s_req_chg_mgr_ck" % _DMN),
                                     nullable=False, default=False)

    __mapper_args__ = {'polymorphic_identity': _DMN,
                       'inherit_condition': domain_id == Branch.id}

domain = Domain.__table__  # pylint: disable=C0103, E1101
domain.primary_key.name = '%s_pk' % _DMN
domain.info['unique_fields'] = ['name']
Domain.tracked_branch = relation(Branch, uselist=False, backref='trackers',
        primaryjoin=Domain.tracked_branch_id == Branch.id)


class Sandbox(Branch):
    """
        Template branch where the checked out contents are managed
        by a user.  Multiple users can have a sandbox checked out.
    """
    __tablename__ = _SBX
    __mapper_args__ = {'polymorphic_identity': _SBX}

    sandbox_id = Column(Integer, ForeignKey('branch.id', name='%s_fk' % _SBX,
                                            ondelete='CASCADE'),
                        primary_key=True)

sandbox = Sandbox.__table__  # pylint: disable=C0103, E1101
sandbox.primary_key.name = '%s_pk' % _SBX
sandbox.info['unique_fields'] = ['name']
