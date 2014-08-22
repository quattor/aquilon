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
"""Contains the logic for `aq show host --list`."""

from sqlalchemy.orm import joinedload, subqueryload, undefer

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostlist_to_hosts,
                                            preload_machine_data)


class CommandShowHostList(BrokerCommand):

    def render(self, session, list, **arguments):
        options = [joinedload('personality'),
                   undefer('personality.archetype.comments'),
                   subqueryload('personality._grns'),
                   subqueryload('_grns'),
                   subqueryload('services_used'),
                   subqueryload('services_provided'),
                   joinedload('resholder'),
                   subqueryload('resholder.resources'),
                   joinedload('_cluster'),
                   subqueryload('_cluster.cluster'),
                   joinedload('hardware_entity.model'),
                   subqueryload('hardware_entity.interfaces'),
                   subqueryload('hardware_entity.interfaces.assignments'),
                   subqueryload('hardware_entity.interfaces.assignments.dns_records'),
                   joinedload('hardware_entity.interfaces.assignments.network'),
                   joinedload('hardware_entity.location'),
                   subqueryload('hardware_entity.location.parents')]
        dbhosts = hostlist_to_hosts(session, list, options)
        preload_machine_data(session, dbhosts)

        return dbhosts
