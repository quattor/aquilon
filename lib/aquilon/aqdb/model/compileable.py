# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
""" Common base for compileable objects. """

from sqlalchemy.ext.declarative import declared_attr

from sqlalchemy import Column, ForeignKey
from sqlalchemy.orm import relation

from aquilon.aqdb.model import Branch, Sandbox, PersonalityStage, User


class CompileableMixin(object):
    @declared_attr
    def branch_id(cls):  # pylint: disable=E0213
        return Column(ForeignKey(Branch.id), nullable=False, index=True)

    @declared_attr
    def sandbox_author_id(cls):  # pylint: disable=E0213
        return Column(ForeignKey(User.id, ondelete="SET NULL"), nullable=True)

    @declared_attr
    def personality_stage_id(cls):  # pylint: disable=E0213
        # Lack of cascaded deletion is intentional on personality
        return Column(ForeignKey(PersonalityStage.id), nullable=False, index=True)

    @declared_attr
    def personality_stage(cls):  # pylint: disable=E0213
        return relation(PersonalityStage, lazy=False, innerjoin=True)

    @declared_attr
    def branch(cls):  # pylint: disable=E0213
        return relation(Branch, lazy=False, innerjoin=True)

    @declared_attr
    def sandbox_author(cls):  # pylint: disable=E0213
        return relation(User)

    @property
    def archetype(self):
        return self.personality.archetype

    @property
    def personality(self):
        return self.personality_stage.personality

    @property
    def authored_branch(self):
        if isinstance(self.branch, Sandbox):
            if self.sandbox_author:
                return "%s/%s" % (self.sandbox_author.name, self.branch.name)
            else:
                return "%s [orphaned]" % self.branch.name
        return self.branch.name

    @property
    def required_services(self):
        rqs = set(self.personality_stage.services)
        rqs.update(self.archetype.services)
        return rqs
