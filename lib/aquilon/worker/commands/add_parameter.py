# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015  Contributor
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

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import (Personality, PersonalityParameter,
                                ParamDefinition, Feature)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.parameter import (set_parameter,
                                                 get_paramdef_for_parameter)
from aquilon.worker.dbwrappers.change_management import validate_prod_personality
from aquilon.worker.templates import Plenary, PlenaryCollection


class CommandAddParameter(BrokerCommand):

    required_parameters = ['personality', 'path']
    strict_path = True

    def process_parameter(self, session, dbstage, db_paramdef, path, value):
        if not dbstage.parameter:
            dbstage.parameter = PersonalityParameter(value={})

        set_parameter(session, dbstage.parameter, db_paramdef, path, value)

    def render(self, session, logger, archetype, personality, personality_stage,
               feature, type, path, user, value=None, justification=None,
               reason=None, **_):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.archetype.is_compileable:
            raise ArgumentError("{0} is not compileable."
                                .format(dbpersonality.archetype))

        dbstage = dbpersonality.active_stage(personality_stage)

        validate_prod_personality(dbstage, user, justification, reason)

        if feature:
            dbfeature = Feature.get_unique(session, name=feature, feature_type=type,
                                           compel=True)
            if dbfeature not in [link.feature for link in dbstage.features]:
                raise ArgumentError("{0} is not bound to {1:l}."
                                    .format(dbfeature, dbstage))
            holders = [dbfeature.param_def_holder]
        else:
            holders = dbpersonality.archetype.param_def_holders.values()

        path = ParamDefinition.normalize_path(path, strict=self.strict_path)

        for param_def_holder in holders:
            db_paramdef = get_paramdef_for_parameter(path, param_def_holder)
            if db_paramdef:
                break
        else:
            raise NotFoundException("Parameter %s does not match any "
                                    "parameter definitions." % path)

        self.process_parameter(session, dbstage, db_paramdef, path, value)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbstage))
        plenaries.write()

        return
