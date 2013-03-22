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


from aquilon.aqdb.model import OperatingSystem, Archetype
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ArgumentError
import re


class CommandAddOS(BrokerCommand):

    required_parameters = ["osname", "osversion", "archetype"]

    def render(self, session, osname, osversion, archetype, comments,
               **arguments):
        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(osname)):
            raise ArgumentError("OS name '%s' is not valid." % osname)
        if not valid.match(osversion):
            raise ArgumentError("OS version '%s' is not valid." % osversion)

        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        OperatingSystem.get_unique(session, name=osname, version=osversion,
                                   archetype=dbarchetype, preclude=True)

        dbos = OperatingSystem(name=osname, version=osversion,
                               archetype=dbarchetype, comments=comments)
        session.add(dbos)

        return
