# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015  Contributor
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
from aquilon.aqdb.model import Personality, Parameter, ArchetypeParamDef
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.parameter import PersonalityProtoParameter


class CommandShowParameterPersonality(BrokerCommand):

    required_parameters = ['personality']

    def render(self, session, personality, personality_stage, archetype,
               style, **arguments):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        dbstage = dbpersonality.default_stage(personality_stage)

        # Unfortunately, the raw and the protobuf formatters operate on
        # different data: the protobuf formatter groups the values per parameter
        # definition, while the raw formatter groups them by the top-level key
        # (which is usually the template name).
        if style == 'proto':
            params = PersonalityProtoParameter()

            for param_def_holder, param in dbstage.parameters.items():
                param_definitions = param_def_holder.param_definitions
                if isinstance(param_def_holder, ArchetypeParamDef):
                    for param_def in param_definitions:
                        value = param.get_path(param_def.path, compel=False)
                        if value is not None:
                            if param_def.value_type == "list":
                                value = ",".join(value)
                            params.append((param_def.path, param_def, value))
                else:
                    for param_def in param_definitions:
                        path = Parameter.feature_path(param_def_holder.feature,
                                                      param_def.path)
                        value = param.get_path(path, compel=False)
                        if value is not None:
                            if param_def.value_type == "list":
                                value = ",".join(value)
                            params.append((path, param_def, value))

            if not params:
                raise NotFoundException("No parameters found for {0:l}."
                                        .format(dbstage))
            return params
        else:
            params = [param for param in dbstage.parameters.values()
                      if param.value]
            if not params:
                raise NotFoundException("No parameters found for {0:l}."
                                        .format(dbstage))

            # List general parameters first sorted by template, then the feature
            # parameters
            params.sort(key=lambda x:
                        (0, x.param_def_holder.template)
                        if isinstance(x.param_def_holder, ArchetypeParamDef) else
                        (1, x.param_def_holder.feature.name))

            return params
