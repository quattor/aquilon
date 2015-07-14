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

from collections import defaultdict

from aquilon.aqdb.model import (ArchetypeParamDef, Parameter, Personality,
                                ServiceMap)
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.parameter import DiffData


class CommandShowDiff(BrokerCommand):

    required_parameters = ["archetype", "personality"]

    def render(self, session, archetype, personality, personality_stage,
               other, other_archetype, other_stage, **arguments):

        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)
        dbstage = dbpersona.default_stage(personality_stage)

        if not other:
            other = personality
        if not other_archetype:
            other_archetype = archetype

        db_other_persona = Personality.get_unique(session, name=other,
                                                  archetype=other_archetype,
                                                  compel=True)
        db_other_ver = db_other_persona.default_stage(other_stage)

        ret = defaultdict(dict)
        self.populate_data(session, dbstage, "my", ret)
        self.populate_data(session, db_other_ver, "other", ret)

        return DiffData(dbstage, db_other_ver, ret)

    def populate_data(self, session, dbstage, dtype, ret):
        """ pouplate data we are interesetd in seeing as part of diff """
        dbpersona = dbstage.personality

        for param_def_holder, parameter in dbstage.parameters.items():
            if isinstance(param_def_holder, ArchetypeParamDef):
                desc = "Parameters for template %s" % param_def_holder.template
            else:
                desc = "Parameters for {0:l}".format(param_def_holder.feature)
            ret[desc][dtype] = Parameter.flatten(parameter.value)

        # process features
        features = {fl.feature.name: True for fl in dbstage.features}
        ret["Features"][dtype] = features

        # process required_services
        services = {srv.name: link.host_environment.name if link.host_environment else None
                    for srv, link in dbstage.required_services.items()}
        ret["Required Services"][dtype] = services

        # service maps
        q = session.query(ServiceMap).filter_by(personality=dbpersona)

        smaps = {"{0} {1}".format(sm.service_instance, sm.location): True for sm in q}

        ret["ServiceMap"][dtype] = smaps

        # grns
        grns = {grn_rec.grn: True for grn_rec in dbstage.grns}
        ret["Grns"][dtype] = grns

        # options
        enabled = defaultdict()
        if dbpersona.config_override:
            enabled["ConfigOverride"] = True
        if dbpersona.cluster_required:
            enabled["Cluster Required"] = True

        enabled["Environment"] = dbpersona.host_environment.name
        ret["Options"][dtype] = enabled
