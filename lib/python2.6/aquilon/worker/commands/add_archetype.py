# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Archetype
from aquilon.exceptions_ import ArgumentError
import re


class CommandAddArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, cluster_type, compilable,
               description, **kwargs):
        valid = re.compile('^[a-zA-Z0-9_-]+$')
        if (not valid.match(archetype)):
            raise ArgumentError("Archetype name '%s' is not valid." % archetype)
        if archetype in ["hardware", "machine", "pan", "t",
                         "service", "servicedata", "clusters"]:
            raise ArgumentError("Archetype name %s is reserved." % archetype)

        Archetype.get_unique(session, archetype, preclude=True)

        if description is None:
            description = archetype
        dbarch = Archetype(name=archetype,
                           cluster_type=cluster_type,
                           outputdesc=description,
                           is_compileable=bool(compilable))

        session.add(dbarch)
        session.flush()

        return
