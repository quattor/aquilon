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
"""Contains the logic for `aq show personality --personality`."""

from sqlalchemy.orm import joinedload

from aquilon.aqdb.model import Personality
from aquilon.worker.broker import BrokerCommand


class CommandShowPersonality(BrokerCommand):

    required_parameters = ['personality']

    def render(self, session, personality, personality_stage, archetype, **_):
        options = [joinedload('archetype'),
                   joinedload('host_environment'),
                   joinedload('owner_grn'),
                   joinedload('stages.required_services.service'),
                   joinedload('stages.features.feature'),
                   joinedload('stages.cluster_infos')]
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype,
                                               query_options=options,
                                               compel=True)
        dbstage = dbpersonality.default_stage(personality_stage)

        # The backref is a weak reference by default, force it to strong
        dbstage.personality  # pylint: disable=W0104

        return dbstage
