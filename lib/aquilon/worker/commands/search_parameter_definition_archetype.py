# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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

from operator import attrgetter

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Archetype


class CommandSearchParameterDefinitionArchetype(BrokerCommand):

    required_parameters = ["archetype"]

    def render(self, session, archetype, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if dbarchetype.paramdef_holder and \
           dbarchetype.paramdef_holder.param_definitions:
            return sorted(dbarchetype.paramdef_holder.param_definitions,
                          key=attrgetter('template', 'path'))

        raise NotFoundException("No parameter definitions found for "
                                "archetype {0}.".format(archetype))
