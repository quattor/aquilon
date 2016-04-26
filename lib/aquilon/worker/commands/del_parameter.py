# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2015,2016  Contributor
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

from jsonschema import validate, ValidationError

from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_parameter import CommandAddParameter
from aquilon.worker.dbwrappers.parameter import validate_rebuild_required


class CommandDelParameter(CommandAddParameter):

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, dbstage, db_paramdef, path, value,
                          plenaries):
        try:
            parameter = dbstage.parameters[db_paramdef.holder]
        except KeyError:
            raise NotFoundException("No parameter of path=%s defined." % path)

        if db_paramdef.activation == 'rebuild':
            validate_rebuild_required(session, path, dbstage)

        parameter.del_path(path)

        if not parameter.value:
            del dbstage.parameters[db_paramdef.holder]
        elif db_paramdef.schema:
            new_value = parameter.get_path(db_paramdef.path, compel=False)
            if new_value is not None:
                try:
                    validate(new_value, db_paramdef.schema)
                except ValidationError as err:
                    raise ArgumentError(err)
