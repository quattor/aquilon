# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014,2016  Contributor
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
""" Helper functions for managing features. """

import os.path

from sqlalchemy.orm import contains_eager, subqueryload

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import FeatureLink, Personality, PersonalityStage
from aquilon.worker.templates import Plenary, PlenaryPersonality
from aquilon.worker.templates.domain import template_branch_basedir


def add_link(session, logger, dbfeature, params):
    FeatureLink.get_unique(session, feature=dbfeature, preclude=True,
                           **params)

    # Binding a feature both at the personality and at the archetype level
    # is not an error, as the templete generation will skip duplicates.
    # Still it is worth to emit a warning so the user is aware of this case.
    q = session.query(FeatureLink)
    q = q.filter_by(feature=dbfeature,
                    model=params.get("model", None))
    if "personality_stage" in params and "interface_name" not in params:
        q = q.filter_by(archetype=params["personality_stage"].archetype,
                        personality_stage=None)
        if q.first():
            logger.client_info("Warning: {0:l} is already bound to {1:l}; "
                               "binding it to {2:l} is redundant."
                               .format(dbfeature,
                                       params["personality_stage"].archetype,
                                       params["personality_stage"]))
    elif "archetype" in params:
        q = q.filter_by(interface_name=None)
        q = q.join(PersonalityStage, Personality)
        q = q.filter_by(archetype=params["archetype"])
        for link in q:
            logger.client_info("Warning: {0:l} is bound to {1:l} which "
                               "is now redundant; consider removing it."
                               .format(dbfeature, link.personality_stage))

    dbfeature.links.append(FeatureLink(**params))


def check_feature_template(config, dbarchetype, dbfeature, dbdomain):
    basedir = template_branch_basedir(config, dbdomain)

    # The broker has no control over the extension used, so we check for
    # everything panc accepts
    for ext in ('pan', 'tpl'):
        if os.path.exists("%s/%s/%s/config.%s" % (basedir, dbarchetype.name,
                                                  dbfeature.cfg_path, ext)):
            return

        # Legacy path for hardware features
        if os.path.exists("%s/%s/%s.%s" % (basedir, dbarchetype.name,
                                           dbfeature.cfg_path, ext)):
            return

    raise ArgumentError("{0} does not have templates present in {1:l} "
                        "for {2:l}.".format(dbfeature, dbdomain, dbarchetype))


def get_affected_plenaries(session, plenaries, personality_stage=None,
                           archetype=None, model=None, interface_name=None):
    if personality_stage:
        plenaries.append(Plenary.get_plenary(personality_stage))
    else:
        q = session.query(PersonalityStage)
        q = q.join(Personality)
        q = q.filter_by(archetype=archetype)
        q = q.options(contains_eager('personality'),
                      subqueryload('personality.root_users'),
                      subqueryload('personality.root_netgroups'))
        q = q.options(PlenaryPersonality.query_options(load_personality=False))
        plenaries.extend(Plenary.get_plenary(dbobj) for dbobj in q)
