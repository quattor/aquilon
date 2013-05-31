# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013  Contributor
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
""" Configuration Branches for Systems """

from datetime import datetime

from sqlalchemy import (Integer, Boolean, DateTime, Sequence, String,
                        Column, ForeignKey, UniqueConstraint, Index)
from sqlalchemy.orm import relation, deferred, backref

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

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    owner = relation(UserPrincipal, innerjoin=True)

    __mapper_args__ = {'polymorphic_on': branch_type}
    __table_args__ = (UniqueConstraint(name, name='%s_uk' % _TN),)

branch = Branch.__table__  # pylint: disable=C0103
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

    allow_manage = Column(Boolean(name="%s_allow_manage_ck" % _DMN),
                          nullable=False, default=True)

    tracked_branch = relation(Branch, foreign_keys=tracked_branch_id,
                              backref=backref('trackers'))

    __table_args__ = (Index("%s_tracked_branch_idx" % _DMN,
                            tracked_branch_id),)
    __mapper_args__ = {'polymorphic_identity': _DMN,
                       'inherit_condition': domain_id == Branch.id}

domain = Domain.__table__  # pylint: disable=C0103
domain.info['unique_fields'] = ['name']


class Sandbox(Branch):
    """
        Template branch where the checked out contents are managed
        by a user.  Multiple users can have a sandbox checked out.
    """
    __tablename__ = _SBX

    sandbox_id = Column(Integer, ForeignKey('branch.id', name='%s_fk' % _SBX,
                                            ondelete='CASCADE'),
                        primary_key=True)

    base_commit = Column(AqStr(40), nullable=False)

    __mapper_args__ = {'polymorphic_identity': _SBX}

sandbox = Sandbox.__table__  # pylint: disable=C0103
sandbox.info['unique_fields'] = ['name']
