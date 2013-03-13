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


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Personality
from aquilon.worker.templates.personality import (PlenaryPersonalityPreFeature,
                                                  PlenaryPersonalityPostFeature,
                                                  PlenaryPersonalityParameter,
                                                  PlenaryPersonalityBase,
                                                  get_parameters_by_tmpl)
from aquilon.exceptions_ import NotFoundException


class CommandCatPersonality(BrokerCommand):

    required_parameters = ["personality"]

    def render(self, generate, session, logger, personality, archetype,
               pre_feature, post_feature, param_tmpl, **kwargs):
        dbpersonality = Personality.get_unique(session, archetype=archetype,
                                               name=personality, compel=True)

        plenary = PlenaryPersonalityBase(dbpersonality, logger=logger)
        if pre_feature:
            plenary = PlenaryPersonalityPreFeature(dbpersonality, logger=logger)

        if post_feature:
            plenary = PlenaryPersonalityPostFeature(dbpersonality, logger=logger)

        if param_tmpl:
            param_templates = get_parameters_by_tmpl(dbpersonality)
            if param_tmpl in param_templates.keys():
                plenary = PlenaryPersonalityParameter(dbpersonality, param_tmpl,
                                                      param_templates[param_tmpl],
                                                      logger=logger)
            else:
                raise NotFoundException("No parameter template %s.tpl found." %
                                        param_tmpl)

        lines = []
        if generate:
            lines.append(plenary._generate_content())
        else:
            lines.append(plenary.read())

        return lines
