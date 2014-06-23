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


from aquilon.worker.formats.parameter import DiffData
from aquilon.aqdb.model import (Parameter, Personality,
                                PersonalityServiceMap)
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.parameter import get_parameters
from collections import defaultdict


class CommandShowDiff(BrokerCommand):

    required_parameters = ["archetype", "personality", "other"]

    def render(self, session, archetype, personality, other,
               other_archetype, **arguments):

        dbpersona = Personality.get_unique(session, name=personality,
                                           archetype=archetype, compel=True)

        if not other_archetype:
            other_archetype = archetype

        db_other_persona = Personality.get_unique(session, name=other,
                                                  archetype=other_archetype,
                                                  compel=True)

        ret = defaultdict(dict)
        self.populate_data(session, dbpersona, "my", ret)
        self.populate_data(session, db_other_persona, "other", ret)

        return DiffData(dbpersona, db_other_persona, ret)

    def populate_data(self, session, dbpersona, dtype, ret):
        """ pouplate data we are interesetd in seeing as part of diff """

        # parameters
        params = {}

        dbpersona_parameters = get_parameters(session, personality=dbpersona)

        for param in dbpersona_parameters:
            params.update(Parameter.flatten(param.value))
        ret["Parameters"][dtype] = params

        # process features
        features = dict((fl.feature.name, True) for fl in dbpersona.features)
        ret["Features"][dtype] = features

        # process required_services
        services = dict((srv.name, True) for srv in dbpersona.services)
        ret["Required Services"][dtype] = services

        # service maps
        q = session.query(PersonalityServiceMap).filter_by(personality=dbpersona)

        smaps = dict(("{0} {1}".format(sm.service_instance, sm.location), True) for sm in q.all())

        ret["ServiceMap"][dtype] = smaps

        # grns
        grns = dict((grn, True) for grn in dbpersona.grns)
        ret["Grns"][dtype] = grns

        # options
        enabled = defaultdict()
        if dbpersona.config_override:
            enabled["ConfigOverride"] = True
        if dbpersona.cluster_required:
            enabled["Cluster Required"] = True

        enabled["Environment"] = dbpersona.host_environment.name
        ret["Options"][dtype] = enabled
