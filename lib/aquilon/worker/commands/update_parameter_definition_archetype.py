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
from aquilon.worker.dbwrappers.parameter import validate_param_definition


class CommandUpdParameterDefintionArchetype(BrokerCommand):

    required_parameters = ["archetype", "path"]

    def render(self, session, logger, archetype, path, required,
               activation, default, description, **kwargs):
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

        if required is not None:
            db_paramdef.required = required
        if activation is not None:
            db_paramdef.activation = activation
        if description is not None:
            db_paramdef.description = description

        if default:
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

            validate_param_definition(db_paramdef.path, db_paramdef.value_type,
                                      default)
            db_paramdef.default = default

            logger.client_info("You need to run 'aq flush --personalities' for "
                               "the change of the default value to take effect.")

        session.flush()

        return
