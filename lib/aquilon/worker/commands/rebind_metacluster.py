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

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.update_cluster import CommandUpdateCluster


class CommandRebindMetaCluster(CommandUpdateCluster):

    required_parameters = ["metacluster", "cluster"]

    def render(self, session, metacluster, cluster, **arguments):
        self.deprecated_command("Command rebind_metacluster is deprecated.  "
                                "Please use update_cluster --metacluster "
                                "instead.", **arguments)

        return CommandUpdateCluster.render(self, session=session,
                                           cluster=cluster,
                                           metacluster=metacluster,
                                           personality=None,
                                           personality_stage=None,
                                           max_members=None, fix_location=None,
                                           down_hosts_threshold=None,
                                           maint_threshold=None, comments=None,
                                           switch=None, virtual_switch=None,
                                           memory_capacity=None,
                                           clear_overrides=None, **arguments)
