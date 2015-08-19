# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2015  Contributor
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
from aquilon.aqdb.model import Parameter, FeatureParamDef
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_parameter import CommandAddParameter
from aquilon.worker.dbwrappers.parameter import validate_rebuild_required


class CommandDelParameter(CommandAddParameter):

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, dbstage, dbparam_def, path,
                          value=None):
        if not dbstage.paramholder or not dbstage.paramholder.parameter:
            raise NotFoundException("No parameter of path=%s defined." % path)

        if dbparam_def.activation == 'rebuild':
            validate_rebuild_required(session, path, dbstage)

        if isinstance(dbparam_def.holder, FeatureParamDef):
            path = Parameter.feature_path(dbparam_def.holder.feature, path)
        dbstage.paramholder.parameter.del_path(path)
