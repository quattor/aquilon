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
"""Contains the logic for `aq cat --personality`."""

from aquilon.aqdb.model import Personality
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.personality import (PlenaryPersonalityPreFeature,
                                                  PlenaryPersonalityPostFeature,
                                                  PlenaryPersonalityParameter,
                                                  PlenaryPersonalityBase,
                                                  ParameterTemplate,
                                                  get_parameters_by_tmpl)


class CommandCatPersonality(BrokerCommand):

    required_parameters = ["personality"]

    def render(self, generate, session, logger, personality, archetype,
               pre_feature, post_feature, param_tmpl, **kwargs):
        dbpersonality = Personality.get_unique(session, archetype=archetype,
                                               name=personality, compel=True)

        if pre_feature:
            plenary = PlenaryPersonalityPreFeature.get_plenary(dbpersonality,
                                                               logger=logger)
        elif post_feature:
            plenary = PlenaryPersonalityPostFeature.get_plenary(dbpersonality,
                                                                logger=logger)
        elif param_tmpl:
            param_templates = get_parameters_by_tmpl(dbpersonality)

            if param_tmpl in param_templates.keys():
                values = param_templates[param_tmpl]
            else:
                values = {}

            ptmpl = ParameterTemplate(dbpersonality, param_tmpl, values)
            plenary = PlenaryPersonalityParameter(ptmpl, logger=logger)
        else:
            plenary = PlenaryPersonalityBase.get_plenary(dbpersonality,
                                                         logger=logger)

        if generate:
            return plenary._generate_content()
        else:
            return plenary.read()
