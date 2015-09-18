# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015  Contributor
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
""" Helper functions for change management """

import re

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import AuthorizationException, ArgumentError
from aquilon.aqdb.model import Host, Cluster, Personality, PersonalityStage
from aquilon.aqdb.model.host_environment import Production

TCM_RE = re.compile(r"^tcm=([0-9]+)$", re.IGNORECASE)
SN_RE = re.compile(r"^sn=([a-z]+[0-9]+)$", re.IGNORECASE)
EMERG_RE = re.compile("emergency")


def validate_justification(user, justification, reason):
    result = None
    for valid_re in [TCM_RE, SN_RE, EMERG_RE]:
        result = valid_re.search(justification)
        if result:
            break
    if not result:
        raise ArgumentError("Failed to parse the justification: expected "
                            "tcm=NNNNNNNNN or sn=XXXNNNNN.")
    if justification == 'emergency' and not reason:
        raise AuthorizationException("Justification of 'emergency' requires "
                                     "--reason to be specified.")

    # TODO: EDM validation
    # edm_validate(result.group(0))


def enforce_justification(user, justification, reason):
    if not justification:
        raise AuthorizationException("The operation has production impact, "
                                     "--justification is required.")
    validate_justification(user, justification, reason)


def validate_prod_personality(dbstage, user, justification, reason):
    session = object_session(dbstage)
    if dbstage.personality.is_cluster:
        q = session.query(Cluster.id)
    else:
        q = session.query(Host.hardware_entity_id)
    q = q.filter_by(personality_stage=dbstage)
    if isinstance(dbstage.host_environment, Production) and q.count() > 0:
        enforce_justification(user, justification, reason)


def validate_prod_archetype(dbarchetype, user, justification, reason):
    session = object_session(dbarchetype)
    prod = Production.get_instance(session)
    if dbarchetype.cluster_type:
        q = session.query(Cluster.id)
    else:
        q = session.query(Host.hardware_entity_id)
    q = q.join(PersonalityStage, Personality)
    q = q.filter_by(host_environment=prod, archetype=dbarchetype)
    if q.count() > 0:
        enforce_justification(user, justification, reason)


def validate_prod_os(dbos, user, justification, reason):
    session = object_session(dbos)
    prod = Production.get_instance(session)
    q = session.query(Host.hardware_entity_id)
    q = q.filter_by(operating_system=dbos)
    q = q.join(PersonalityStage, Personality)
    q = q.filter_by(host_environment=prod)
    if q.count() > 0:
        enforce_justification(user, justification, reason)


def validate_prod_service_instance(dbinstance, user, justification, reason):
    session = object_session(dbinstance)
    prod = Production.get_instance(session)

    q1 = session.query(Cluster.id)
    q1 = q1.filter(Cluster.services_used.contains(dbinstance))
    q1 = q1.join(PersonalityStage, Personality)
    q1 = q1.filter_by(host_environment=prod)

    q2 = session.query(Host.hardware_entity_id)
    q2 = q2.filter(Host.services_used.contains(dbinstance))
    q2 = q2.join(PersonalityStage, Personality)
    q2 = q2.filter_by(host_environment=prod)

    if q1.count() > 0 or q2.count() > 0:
        enforce_justification(user, justification, reason)
