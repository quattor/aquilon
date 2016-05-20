# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
"""Contains the logic for `aq show map --all`."""

from sqlalchemy.orm import joinedload, subqueryload
from sqlalchemy.orm.attributes import set_committed_value

from aquilon.aqdb.model import (Location, Rack, City, Personality, ServiceMap,
                                Network)
from aquilon.worker.broker import BrokerCommand


class CommandShowMapAll(BrokerCommand):

    required_parameters = []

    def render(self, session, style, **_):
        q = session.query(Location)
        # Pre-load subclasses which have additional attributes
        q = q.with_polymorphic([Rack, City])
        q = q.join(ServiceMap)
        if style != 'raw':
            q = q.options(subqueryload('parents'))

        loc_by_id = {row.id: row for row in q}

        q = session.query(Personality)
        q = q.join(ServiceMap)

        pers_by_id = {row.id: row for row in q}

        q = session.query(Network)
        q = q.join(ServiceMap)
        if style != 'raw':
            q = q.options(joinedload('network_compartment'),
                          joinedload('location'),
                          subqueryload('routers'),
                          subqueryload('dynamic_stubs'))

        net_by_id = {row.id: row for row in q}

        results = []

        q = session.query(ServiceMap)
        q = q.options(joinedload('service_instance'))

        # Populate properties we already know
        for entry in q:
            try:
                set_committed_value(entry, 'personality',
                                    pers_by_id[entry.personality_id])
            except KeyError:
                pass

            try:
                set_committed_value(entry, 'location',
                                    loc_by_id[entry.location_id])
            except KeyError:
                pass

            try:
                set_committed_value(entry, 'network',
                                    net_by_id[entry.network_id])
            except KeyError:
                pass

            results.append(entry)

        return results
