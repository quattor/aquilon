# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016  Contributor
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

import shlex

from sqlalchemy.orm.session import object_session

from aquilon.exceptions_ import AuthorizationException, ProcessException
from aquilon.aqdb.model import (Host, Cluster, Archetype, Personality,
                                PersonalityStage)
from aquilon.aqdb.model.host_environment import Production
from aquilon.worker.processes import run_command
from aquilon.config import Config


def validate_justification(user, justification, reason, logger):
    config = Config()
    check_enabled = False
    if config.has_option("change_management", "enable"):
        check_enabled = config.getboolean("change_management", "enable")

    justification.check_reason(reason)

    if check_enabled:
        change_management_validate(user, justification, logger, config)


def change_management_validate(user, justification, logger, config):
    check_enforced = False
    if config.has_option("change_management", "enforce"):
        check_enforced = config.getboolean("change_management", "enforce")

    extra_options = ""
    if config.has_option("change_management", "extra_options"):
        extra_options = config.get("change_management", "extra_options")

    cmd = ["checkedm",
           "--resource-instance", "prod",
           "--output-format", "json",
           "--requestor", user]
    if justification.tcm is not None:
        cmd.extend(["--ticketing-system", "TCM2", "--ticket", justification.tcm])
    elif justification.sn is not None:
        cmd.extend(["--ticketing-system", "SN", "--ticket", justification.sn])
    if justification.emergency:
        cmd.append("--emergency")

    cmd.extend(shlex.split(extra_options))

    exception_happened = False
    try:
        out = run_command(cmd)
    except ProcessException as err:
        exception_happened = True
        out = err.out

    logger.info("EDM validation done, request {}; output='{}'".format("denied" if exception_happened else "approved", out))

    if exception_happened:
        if check_enforced:
            raise AuthorizationException("Authorization error")
        else:
            logger.client_info("Change management would reject the justification; reason={0:s}".format(out))


def enforce_justification(user, justification, reason, logger):
    if not justification:
        raise AuthorizationException("The operation has production impact, "
                                     "--justification is required.")
    validate_justification(user, justification, reason, logger)


def validate_prod_personality(dbstage, user, justification, reason, logger):
    session = object_session(dbstage)
    if dbstage.personality.is_cluster:
        q = session.query(Cluster.id)
    else:
        q = session.query(Host.hardware_entity_id)
    q = q.filter_by(personality_stage=dbstage)
    if isinstance(dbstage.host_environment, Production) and q.count() > 0:
        enforce_justification(user, justification, reason, logger)


def validate_prod_archetype(dbarchetype, user, justification, reason, logger):
    session = object_session(dbarchetype)
    prod = Production.get_instance(session)
    if dbarchetype.cluster_type:
        q = session.query(Cluster.id)
    else:
        q = session.query(Host.hardware_entity_id)
    q = q.join(PersonalityStage, Personality)
    q = q.filter_by(host_environment=prod, archetype=dbarchetype)
    if q.count() > 0:
        enforce_justification(user, justification, reason, logger)


def validate_prod_os(dbos, user, justification, reason, logger):
    session = object_session(dbos)
    prod = Production.get_instance(session)
    q = session.query(Host.hardware_entity_id)
    q = q.filter_by(operating_system=dbos)
    q = q.join(PersonalityStage, Personality)
    q = q.filter_by(host_environment=prod)
    if q.count() > 0:
        enforce_justification(user, justification, reason, logger)


def validate_prod_service_instance(dbinstance, user, justification, reason, logger):
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
        enforce_justification(user, justification, reason, logger)


def validate_prod_feature(dbfeature, user, justification, reason, logger):
    session = object_session(dbfeature)
    prod = Production.get_instance(session)

    q = session.query(Archetype)
    q = q.join(Archetype.features)
    q = q.filter_by(feature=dbfeature)
    for dbarchetype in q:
        validate_prod_archetype(dbarchetype, user, justification, reason, logger)

    q1 = session.query(Cluster.id)
    q1 = q1.join(PersonalityStage, Personality)
    q1 = q1.filter_by(host_environment=prod)
    q1 = q1.join(PersonalityStage.features)
    q1 = q1.filter_by(feature=dbfeature)

    # This ignores model and interface name restrictions. That means we may
    # require --justification even if no actual host is impacted - we can live
    # with that.
    q2 = session.query(Host.hardware_entity_id)
    q2 = q2.join(PersonalityStage, Personality)
    q2 = q2.filter_by(host_environment=prod)
    q2 = q2.join(PersonalityStage.features)
    q2 = q2.filter_by(feature=dbfeature)

    if q1.count() > 0 or q2.count() > 0:
        enforce_justification(user, justification, reason, logger)
