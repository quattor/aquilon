# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013,2014,2015,2016  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Personality, PersonalityParameter,
                                ParamDefinition, ArchetypeParamDef, Feature)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.change_management import validate_prod_personality
from aquilon.worker.dbwrappers.feature import get_affected_plenaries
from aquilon.worker.dbwrappers.parameter import (set_parameter,
                                                 lookup_paramdef)


class CommandAddParameter(BrokerCommand):
    requires_plenaries = True

    required_parameters = ['personality', 'path']

    def process_parameter(self, session, dbstage, db_paramdef, path, value,
                          plenaries):
        try:
            parameter = dbstage.parameters[db_paramdef.holder]
        except KeyError:
            parameter = PersonalityParameter(param_def_holder=db_paramdef.holder,
                                             value={})
            dbstage.parameters[db_paramdef.holder] = parameter

            # Since the parameter is new, the PlenaryPersonality collection does
            # not have it, so we need to add it explicitly for the template to
            # get created on the disk. It would be nice if PlanaryPersonality
            # would be able to handle this internally, but that would need
            # deeper surgery.
            if isinstance(db_paramdef.holder, ArchetypeParamDef):
                plenaries.add(parameter)

        set_parameter(session, parameter, db_paramdef, path, value)

    def render(self, session, plenaries, archetype, personality, personality_stage,
               feature, type, path, user, value=None, justification=None,
               reason=None, **_):
        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        dbpersonality.archetype.require_compileable("parameters are not supported")

        dbstage = dbpersonality.active_stage(personality_stage)

        validate_prod_personality(dbstage, user, justification, reason)

        path = ParamDefinition.normalize_path(path, strict=False)

        plenaries.add(dbstage)

        if feature:
            dbfeature = Feature.get_unique(session, name=feature, feature_type=type,
                                           compel=True)
            if dbfeature not in dbstage.param_features:
                raise ArgumentError("{0} is not bound to {1:l}, or it does not "
                                    "have any parameters defined."
                                    .format(dbfeature, dbstage))
            holder_object = dbfeature

            for link in dbstage.features:
                if link.feature != dbfeature:
                    continue

                get_affected_plenaries(session, dbfeature, plenaries, dbstage,
                                       None, link.model, link.interface_name)
        else:
            holder_object = dbpersonality.archetype

        db_paramdef, rel_path = lookup_paramdef(holder_object, path, False)

        self.process_parameter(session, dbstage, db_paramdef, rel_path, value,
                               plenaries)

        session.flush()

        plenaries.write()

        return
