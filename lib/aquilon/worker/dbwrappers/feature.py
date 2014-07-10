# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import FeatureLink, Personality

from aquilon.worker.templates.domain import template_branch_basedir


def model_features(dbmodel, dbarch, dbpers, interface_name=None):
    features = []
    for link in dbmodel.features:
        if (link.archetype is None or link.archetype == dbarch) and \
           (link.personality is None or link.personality == dbpers) and \
           (link.interface_name is None or link.interface_name == interface_name):
            features.append(link.feature)

    return features


def personality_features(dbpersonality):
    pre = []
    post = []
    for link in dbpersonality.archetype.features:
        if link.model or link.interface_name:
            continue
        if link.feature.post_personality:
            post.append(link.feature)
        else:
            pre.append(link.feature)

    for link in dbpersonality.features:
        if link.model or link.interface_name:
            continue
        if link.feature.post_personality:
            if link.feature in post:
                continue
            post.append(link.feature)
        else:
            if link.feature in pre:
                continue
            pre.append(link.feature)

    return (pre, post)


def interface_features(dbinterface, dbarch, dbpers):
    features = []

    if dbinterface.model_allowed:
        # Add features bound to the model
        for feature in model_features(dbinterface.model, dbarch, dbpers,
                                      dbinterface.name):
            if feature not in features:
                features.append(feature)

    if dbpers:
        # Add features bound to the personality, if the interface name matches
        for link in dbpers.features:
            # Model features were handled above
            if link.model:
                continue
            if link.interface_name != dbinterface.name:
                continue
            if link.feature not in features:
                features.append(link.feature)

    return features


def add_link(session, logger, dbfeature, params):
    FeatureLink.get_unique(session, feature=dbfeature, preclude=True,
                           **params)

    # Binding a feature both at the personality and at the archetype level
    # is not an error, as the templete generation will skip duplicates.
    # Still it is worth to emit a warning so the user is aware of this case.
    q = session.query(FeatureLink)
    q = q.filter_by(feature=dbfeature,
                    model=params.get("model", None))
    if "personality" in params and "interface_name" not in params:
        q = q.filter_by(archetype=params["personality"].archetype,
                        personality=None)
        if q.first():
            logger.client_info("Warning: {0:l} is already bound to {1:l}; "
                               "binding it to {2:l} is redundant."
                               .format(dbfeature,
                                       params["personality"].archetype,
                                       params["personality"]))
    elif "archetype" in params:
        q = q.filter_by(interface_name=None)
        q = q.join(Personality)
        q = q.filter_by(archetype=params["archetype"])
        for link in q.all():
            logger.client_info("Warning: {0:l} is bound to {1:l} which "
                               "is now redundant; consider removing it."
                               .format(dbfeature, link.personality))

    dbfeature.links.append(FeatureLink(**params))


def check_feature_template(config, dbarchetype, dbfeature, dbdomain):
    basedir = template_branch_basedir(config, dbdomain)

    # The broker has no control over the extension used, so we check for
    # everything panc accepts
    for ext in ('pan', 'tpl'):
        if os.path.exists("%s/%s/%s/config.%s" % (basedir, dbarchetype.name,
                                                  dbfeature.cfg_path, ext)):
            return

    raise ArgumentError("{0} does not have templates present in {1:l} "
                        "for {2:l}.".format(dbfeature, dbdomain, dbarchetype))
