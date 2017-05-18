# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2012,2013,2014,2015,2016  Contributor
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
                        Column, ForeignKey, PrimaryKeyConstraint)
from sqlalchemy.orm import relation, deferred, backref, validates

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Base, UserPrincipal
from aquilon.aqdb.column_types import AqStr

_TN = "branch"
_DMN = "domain"
_SBX = "sandbox"
_RV = "review"


class Branch(Base):
    """
        Each branch of template-king represents a distinct set of
        templates in use broker-side (domains) or client-side (sandboxes)
        for testing and managing systems.
    """
    __tablename__ = _TN

    id = Column(Integer, Sequence('%s_id_seq' % _TN), primary_key=True)

    branch_type = Column(AqStr(16), nullable=False)

    name = Column(AqStr(32), nullable=False, unique=True)

    compiler = Column(String(255), nullable=False)

    is_sync_valid = Column(Boolean, nullable=False, default=True)

    autosync = Column(Boolean, nullable=False, default=True)

    formats = Column(AqStr(16), nullable=True)

    creation_date = deferred(Column(DateTime, default=datetime.now,
                                    nullable=False))

    comments = deferred(Column(String(255), nullable=True))

    __table_args__ = ({'info': {'unique_fields': ['name']}},)
    __mapper_args__ = {'polymorphic_on': branch_type}

    @validates("formats")
    def _validate_formats(self, key, value):  # pylint: disable=W0613
        if not value:
            return None
        formats = value.strip().lower().split(",")
        for format in formats:
            if format not in ["pan", "json"]:
                raise ArgumentError("Unknown format: %s" % format)
        return ",".join(formats)


class Domain(Branch):
    """
        Template branch where the checked out contents are managed
        solely by the broker.
    """
    __tablename__ = _DMN

    branch_id = Column(ForeignKey(Branch.id, ondelete='CASCADE'),
                       primary_key=True)

    tracked_branch_id = Column(ForeignKey(Branch.id,
                                          name='%s_tracked_branch_fk' % _DMN),
                               nullable=True, index=True)
    rollback_commit = Column(AqStr(40), nullable=True)

    requires_change_manager = Column(Boolean, nullable=False, default=False)

    allow_manage = Column(Boolean, nullable=False, default=True)

    archived = Column(Boolean, nullable=False, default=False)

    tracked_branch = relation(Branch, foreign_keys=tracked_branch_id,
                              backref=backref('trackers'))

    auto_compile = Column(Boolean, nullable=False, default=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)
    __mapper_args__ = {'polymorphic_identity': _DMN,
                       'inherit_condition': branch_id == Branch.id}


class Sandbox(Branch):
    """
        Template branch where the checked out contents are managed
        by a user.  Multiple users can have a sandbox checked out.
    """
    __tablename__ = _SBX

    branch_id = Column(ForeignKey(Branch.id, ondelete='CASCADE'),
                       primary_key=True)

    owner_id = Column(ForeignKey(UserPrincipal.id), nullable=False, index=True)

    base_commit = Column(AqStr(40), nullable=False)

    owner = relation(UserPrincipal, innerjoin=True)

    __table_args__ = ({'info': {'unique_fields': ['name']}},)
    __mapper_args__ = {'polymorphic_identity': _SBX}


class Review(Base):
    __tablename__ = _RV
    _class_label = 'Review Request'

    source_id = Column(Integer, ForeignKey(Branch.id, ondelete="CASCADE"),
                       nullable=False)
    target_id = Column(Integer, ForeignKey(Domain.branch_id, ondelete="CASCADE"),
                       nullable=False, index=True)

    commit_id = Column(AqStr(40), nullable=False)

    testing_url = Column(String(255), nullable=True)
    target_commit_id = Column(AqStr(40), nullable=True)
    tested = Column(Boolean, nullable=True)

    review_url = Column(String(255), nullable=True)

    approved = Column(Boolean, nullable=True)

    target = relation(Domain, innerjoin=True, foreign_keys=target_id)

    source = relation(Branch, innerjoin=True, foreign_keys=source_id,
                      backref=backref('reviews',
                                      cascade="all, delete-orphan",
                                      passive_deletes=True))

    __table_args__ = (PrimaryKeyConstraint(source_id, target_id),
                      {'info': {'unique_fields': ['source', 'target']}})
