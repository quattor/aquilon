# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2014,2015,2016,2017  Contributor
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

from sqlalchemy.orm import aliased, object_session
from sqlalchemy.sql import or_

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Archetype, Personality, PersonalityStage,
                                ClusterLifecycle, Cluster, Host, HardwareEntity,
                                Location, Building, BuildingPreference)
from aquilon.worker.dbwrappers.branch import get_branch_and_author


def parse_cluster_arguments(session, config, archetype, personality,
                            personality_stage, domain, sandbox, buildstatus,
                            max_members):
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

    if not domain and not sandbox:  # pragma: no cover
        raise ArgumentError("There is no default domain configured for "
                            "{0:l}, please specify --domain or --sandbox."
                            .format(dbarchetype))

    dbbranch, dbauthor = get_branch_and_author(session, domain=domain,
                                               sandbox=sandbox, compel=True)

    if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
        raise ArgumentError("Adding clusters to {0:l} is not allowed."
                            .format(dbbranch))

    if max_members is None and config.has_option(section, "max_members_default"):
        max_members = config.getint(section, "max_members_default")

    kw = {'personality_stage': dbpersonality.default_stage(personality_stage),
          'branch': dbbranch,
          'sandbox_author': dbauthor,
          'status': dbstatus,
          'max_members': max_members}

    return kw


def get_clusters_by_locations(session, locations, archetype):
    """
    Return clusters which has members inside all the locations specified.

    The most common use case is looking for clusters which span a given pair
    of buildings, but nothing below is limited to buildings or only two
    locations.
    """
    q = session.query(Cluster)
    q = q.join(PersonalityStage, Personality)
    q = q.filter_by(archetype=archetype)
    q = q.reset_joinpoint()

    for side in locations:
        HWLoc = aliased(Location)
        Parent = aliased(Location)

        q1 = session.query(Cluster.id)
        q1 = q1.join(Cluster._hosts, Host, HardwareEntity)
        q1 = q1.join(HWLoc, HardwareEntity.location)
        q1 = q1.outerjoin(Parent, HWLoc.parents)
        q1 = q1.filter(or_(HWLoc.id == side.id, Parent.id == side.id))

        q = q.filter(Cluster.id.in_(q1.subquery()))

    # TODO: Add eager-loading options
    return q.all()


def get_cluster_location_preference(dbcluster):
    if dbcluster.preferred_location:
        return dbcluster.preferred_location

    if not dbcluster.archetype.has_building_preferences:
        return None

    buildings = dbcluster.member_locations(location_class=Building)
    if not buildings or len(buildings) != 2:
        return None

    pair = BuildingPreference.ordered_pair(buildings)
    session = object_session(dbcluster)
    db_pref = BuildingPreference.get_unique(session, building_pair=pair,
                                            archetype=dbcluster.archetype)
    if db_pref:
        return db_pref.prefer
    else:
        return None


def check_cluster_priority_order(dbcluster, config, priority_parameter, priord):
    section = "archetype_" + dbcluster.archetype.name
    try:
        cpri_min = int(config.get(section, "min_priority_order"))
        cpri_max = int(config.get(section, "max_priority_order"))
        cpri_src = "configured"
    except (NoSectionError, NoOptionError):
        cpri_min = 1
        cpri_max = 99
        cpri_src = "built-in"

    if (int(priord) < cpri_min) or (int(priord) > cpri_max):
        raise ArgumentError("Value for {0} ({1}) is outside of the {2} range "
                            "{3}..{4}".format(priority_parameter, priord,
                                              cpri_src, cpri_min, cpri_max))

    return (cpri_min, cpri_max, cpri_src)
