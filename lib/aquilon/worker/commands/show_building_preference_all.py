# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016 Contributor
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
""" Contains the logic for `aq show building preference --all`. """

from sqlalchemy.orm import aliased, contains_eager

from aquilon.aqdb.model import BuildingPreference, Building, Archetype
from aquilon.worker.broker import BrokerCommand


class CommandShowBuildingPreferenceAll(BrokerCommand):

    def render(self, session, **_):
        AB = aliased(Building)
        BB = aliased(Building)

        q = session.query(BuildingPreference)
        q = q.join(AB, BuildingPreference.a)
        q = q.join(BB, BuildingPreference.b)
        q = q.join(Archetype)
        q = q.options(contains_eager('a', alias=AB),
                      contains_eager('b', alias=BB),
                      contains_eager('archetype'))
        q = q.order_by(AB.name, BB.name, Archetype.name)
        return q.all()
