# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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


from aquilon.worker.formats.parameter_definition import ParamDefinitionFormatter
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import FeatureLinkParameter, PersonalityParameter
from aquilon.worker.dbwrappers.parameter import (get_parameter_holder,
                                                 get_parameters)
from aquilon.exceptions_ import ArgumentError


class CommandValidateParameter(BrokerCommand):

    def render(self, session, logger, personality, archetype, feature,
               **arguments):

        if not personality:
            if not feature:
                raise ArgumentError("Parameters can be validated for "
                                    "personality or feature.")
            if not archetype:
                raise ArgumentError("Validating parameter on feature binding "
                                    "needs personality or archetype.")

        param_holder = get_parameter_holder(session, archetype, personality,
                                            feature)

        if isinstance(param_holder, FeatureLinkParameter):
            paramdef_holder = param_holder.featurelink.feature.paramdef_holder
            parameters = get_parameters(session,
                                        featurelink=param_holder.featurelink)
        elif isinstance(param_holder, PersonalityParameter):
            paramdef_holder = param_holder.personality.archetype.paramdef_holder
            parameters = get_parameters(session,
                                        personality=param_holder.personality)
        else:
            paramdef_holder = None
            parameters = []

        if paramdef_holder:
            param_definitions = paramdef_holder.param_definitions
        else:
            param_definitions = []

        errors = []
        formatter = ParamDefinitionFormatter()

        for param_def in param_definitions:
            ## ignore not required fields or fields
            ## which have defaults specified
            if (not param_def.required) or param_def.default:
                continue

            value = None
            for param in parameters:
                value = param.get_path(param_def.path, compel=False)
                if value:
                    break

            ## ignore if value is specified
            if value is None:
                errors.append(formatter.format_raw(param_def))

        if errors:
            raise ArgumentError("Following required parameters have not been "
                                "specified:\n" +
                                "\n".join([error for error in errors]))

        logger.client_info("All required parameters specified.")
        return
