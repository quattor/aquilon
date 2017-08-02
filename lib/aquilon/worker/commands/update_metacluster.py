# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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

from aquilon.aqdb.model import MetaCluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.update_cluster import CommandUpdateCluster
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateMetaCluster(CommandUpdateCluster):
    requires_plenaries = True

    required_parameters = ["metacluster"]

    def render(self, session, plenaries, metacluster, personality,
               personality_stage, max_members,
               fix_location, clear_location_preference,
               virtual_switch, comments, user, justification, reason,
               logger, **arguments):
        dbmetacluster = MetaCluster.get_unique(session, metacluster,
                                               compel=True)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbmetacluster)
        cm.validate()

        self.update_cluster_common(session, dbmetacluster, plenaries,
                                   personality, personality_stage, max_members,
                                   fix_location, clear_location_preference,
                                   virtual_switch, comments, **arguments)

        session.flush()
        dbmetacluster.validate()

        plenaries.write()

        return
