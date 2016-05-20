# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import Archetype, ParamDefinition
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_archetype
from aquilon.worker.dbwrappers.parameter import (add_arch_paramdef_plenaries,
                                                 update_paramdef_schema)
from aquilon.worker.templates import PlenaryCollection


class CommandUpdParameterDefintionArchetype(BrokerCommand):

    required_parameters = ["archetype", "path"]

    def render(self, session, logger, archetype, path, schema, clear_schema,
               required, activation, default, clear_default, description, user,
               justification, reason, **_):
        dbarchetype = Archetype.get_unique(session, archetype, compel=True)
        if not dbarchetype.is_compileable:
            raise ArgumentError("{0} is not compileable.".format(dbarchetype))

        path = ParamDefinition.normalize_path(path)
        for holder in dbarchetype.param_def_holders.values():
            db_paramdef = ParamDefinition.get_unique(session, path=path,
                                                     holder=holder)
            if db_paramdef:
                break
        else:
            raise ArgumentError("Parameter definition %s not found." % path)

        plenaries = PlenaryCollection(logger=logger)

        # Changing the default value impacts all personalities which do not
        # override it, so more scrunity is needed
        if default is not None or clear_default:
            # Changing the default of a parameter which requires a rebuild is
            # a risky operation. If it is really needed, then the workaround is
            # to turn the activation flag off first, update the value, and
            # turn activation back again.
            if db_paramdef.activation == 'rebuild':
                raise UnimplementedError("Changing the default value of a "
                                         "parameter which requires rebuild "
                                         "would cause all existing hosts to "
                                         "require a rebuild, which is not "
                                         "supported.")

            validate_prod_archetype(dbarchetype, user, justification, reason)
            add_arch_paramdef_plenaries(session, dbarchetype,
                                        db_paramdef.holder, plenaries)

            db_paramdef.default = default

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

        plenaries.write(verbose=True)

        return
