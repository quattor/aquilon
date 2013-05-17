# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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

from aquilon.aqdb.model import (ParamDefinition,
                                Archetype)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import search_path_in_personas
from aquilon.worker.formats.parameter import SimpleParameterList


class CommandSearchParameter(BrokerCommand):

    required_parameters = ['path']

    def render(self, session, archetype, path, **arguments):

        db_paramdef = None

        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            if not dbarchetype.paramdef_holder:
                return
            db_paramdef = ParamDefinition.get_unique(session, path=path,
                                                     holder=dbarchetype.paramdef_holder,
                                                     compel=True)
        if not db_paramdef:
            return


        holder = search_path_in_personas(session, path, db_paramdef.holder)
        return SimpleParameterList(holder.iteritems())
