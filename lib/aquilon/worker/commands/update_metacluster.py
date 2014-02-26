# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
from aquilon.aqdb.model import MetaCluster, Personality
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.update_cluster import update_cluster_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    def render(self, session, logger, metacluster, personality, max_members,
               fix_location, high_availability, comments, **arguments):
        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmetacluster))

        if personality:
            archetype = dbmetacluster.personality.archetype.name
            dbpersonality = Personality.get_unique(session, name=personality,
                                                   archetype=archetype,
                                                   compel=True)
            if not dbpersonality.is_cluster:
                raise ArgumentError("Personality {0} is not a cluster " +
                                    "personality".format(dbpersonality))
            dbmetacluster.personality = dbpersonality

        if max_members is not None:
            dbmetacluster.max_clusters = max_members

        if comments is not None:
            dbmetacluster.comments = comments

        if high_availability is not None:
            dbmetacluster.high_availability = high_availability

        # TODO update_cluster_location would update VMs. Metaclusters
        # will contain VMs in Vulcan2 model.
        update_cluster_location(session, logger, dbmetacluster, fix_location,
                                plenaries, **arguments)

        session.flush()
        dbmetacluster.validate()

        plenaries.write(locked=False)

        return
