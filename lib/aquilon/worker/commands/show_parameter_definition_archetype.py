# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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

from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import Archetype, ParamDefinition
from aquilon.worker.broker import BrokerCommand


class CommandShowParameterDefinitionArchetype(BrokerCommand):

    required_parameters = ["archetype", "path"]

    def render(self, session, archetype, path, **arguments):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not dbarchetype.param_def_holder:
            raise NotFoundException("{0} does not have parameters."
                                    .format(dbarchetype))

        dbparam_def = ParamDefinition.get_unique(session,
                                                 holder=dbarchetype.param_def_holder,
                                                 path=path, compel=True)
        return dbparam_def
