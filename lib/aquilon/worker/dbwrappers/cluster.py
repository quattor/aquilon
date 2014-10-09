# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014  Contributor
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
from aquilon.aqdb.model import Archetype, Personality, ClusterLifecycle
from aquilon.worker.dbwrappers.branch import get_branch_and_author


def parse_cluster_arguments(session, config, archetype, personality, domain, sandbox,
                            buildstatus, max_members):
    dbarchetype = Archetype.get_unique(session, archetype, compel=True)
    section = "archetype_" + dbarchetype.name

    if not personality:
        if config.has_option(section, "default_personality"):
            personality = config.get(section, "default_personality")
    if not personality:
        raise ArgumentError("There is no default personality configured "
                            "for {0:l}, please specify --personality."
                            .format(dbarchetype))

    dbpersonality = Personality.get_unique(session, name=personality,
                                           archetype=dbarchetype, compel=True)
    if not dbpersonality.is_cluster:
        raise ArgumentError("%s is not a cluster personality." %
                            personality)

    if not buildstatus:
        buildstatus = "build"
    dbstatus = ClusterLifecycle.get_instance(session, buildstatus)

    if not domain and not sandbox and \
       config.has_option(section, "default_domain"):
        domain = config.get(section, "default_domain")

    dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                               sandbox=sandbox, compel=True)

    if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
        raise ArgumentError("Adding clusters to {0:l} is not allowed."
                            .format(dbbranch))

    if max_members is None and config.has_option(section, "max_members_default"):
        max_members = config.getint(section, "max_members_default")

    kw = {'personality_stage': dbpersonality.default_stage,
          'branch': dbbranch,
          'sandbox_author': dbauthor,
          'status': dbstatus,
          'max_members': max_members}

    return kw
