# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import MetaCluster
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.commands.update_cluster import update_cluster_location
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandUpdateMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    def render(self, session, logger, metacluster, max_members,
               fix_location, high_availability, comments, **arguments):
        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)
        cluster_updated = False

        if max_members is not None:
            current_members = len(dbmetacluster.members)
            if max_members < current_members:
                raise ArgumentError("%s has %d clusters bound, which exceeds "
                                    "the requested limit %d." %
                                    (format(dbmetacluster), current_members,
                                     max_members))
            dbmetacluster.max_clusters = max_members
            cluster_updated = True

        if comments is not None:
            dbmetacluster.comments = comments
            cluster_updated = True

        if high_availability is not None:
            dbmetacluster.high_availability = high_availability
            cluster_updated = True

        # TODO update_cluster_location would update VMs. Metaclusters
        # will contain VMs in Vulcan2 model.
        plenaries = PlenaryCollection(logger=logger)
        remove_plenaries = PlenaryCollection(logger=logger)

        location_updated = update_cluster_location(session, logger,
                                                   dbmetacluster, fix_location,
                                                   plenaries, remove_plenaries,
                                                   **arguments)

        if location_updated:
            cluster_updated = True

        if not cluster_updated:
            return

        session.add(dbmetacluster)
        session.flush()
        dbmetacluster.validate()

        plenary_info = Plenary.get_plenary(dbmetacluster, logger=logger)
        plenary_info.write()

        return
