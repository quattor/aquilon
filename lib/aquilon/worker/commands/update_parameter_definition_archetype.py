# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from aquilon.exceptions_ import UnimplementedError
from aquilon.aqdb.model import Archetype, ParamDefinition
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import (lookup_paramdef,
                                                 update_paramdef_schema)
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdParameterDefintionArchetype(BrokerCommand):

    required_parameters = ["archetype", "path"]

    def render(self, session, archetype, path, schema, clear_schema, required,
               activation, default, clear_default, description,
               user, justification, reason, logger, **_):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        dbarchetype.require_compileable("parameters are not supported")

        # Validate ChangeManagement
        if required is not None:
            cm = ChangeManagement(session, user, justification, reason, logger, self.command)
            cm.consider(dbarchetype)
            cm.validate()

        if default is not None or clear_default:
            raise UnimplementedError("Archetype-wide parameter definitions "
                                     "cannot have default values.")

        path = ParamDefinition.normalize_path(path)
        db_paramdef, _ = lookup_paramdef(dbarchetype, path)

        if required is not None:
            db_paramdef.required = required
        if activation is not None:
            db_paramdef.activation = activation
        if description is not None:
            db_paramdef.description = description
        if schema:
            update_paramdef_schema(session, db_paramdef, schema)
        elif clear_schema:
            db_paramdef.schema = None

        session.flush()

        return
