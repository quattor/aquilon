# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016,2017  Contributor
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
"""Contains the logic for `aq show personality --all`."""

from sqlalchemy.orm import joinedload, subqueryload, contains_eager, undefer

from aquilon.aqdb.model import Personality, PersonalityStage, Archetype
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList


class CommandShowPersonality(BrokerCommand):

    required_parameters = ['all']

    def render(self, session, style, **_):
        q = session.query(PersonalityStage)
        q = q.join(Personality, Archetype)
        q = q.order_by(Archetype.name, Personality.name, PersonalityStage.name)
        q = q.options(contains_eager('personality'),
                      contains_eager('personality.archetype'))

        if style != 'raw':
            q = q.options(subqueryload('required_services'),
                          joinedload('required_services.service'),
                          subqueryload('grns'),
                          subqueryload('features'),
                          joinedload('features.feature'),
                          joinedload('features.model'),
                          undefer('features.feature.comments'),
                          joinedload('cluster_infos'),
                          subqueryload('personality.archetype.required_services'))
            return q.all()
        else:
            return StringAttributeList(q.all(), "qualified_name")
