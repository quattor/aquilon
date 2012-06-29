# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Helper functions for managing features. """

from aquilon.aqdb.model import FeatureLink, Personality


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

