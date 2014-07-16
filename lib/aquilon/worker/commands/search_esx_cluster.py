# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013  Contributor
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
"""Contains the logic for `aq search esx cluster`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.search_cluster import CommandSearchCluster


class CommandSearchESXCluster(CommandSearchCluster):

    required_parameters = []

    def render(self, **arguments):
        gen_arguments = {}

        esx_hostname = None

        # translate option names for search cluster command.
        for key in arguments:
            # change locations prefix
            if key.startswith('vmhost_'):
                gen_arguments[key.replace('vmhost_', 'member_')] = \
                    arguments[key]
            # esx_hostname > member_hostname
            elif key == 'esx_hostname':
                esx_hostname = arguments[key]
            # 'esx_' prefix to these options.
            elif key in ['metacluster', 'guest', 'switch', 'virtual_machine']:
                gen_arguments["esx_%s" % key] = arguments[key]
            else:
                gen_arguments[key] = arguments[key]

            # Backwards compat
            gen_arguments['esx_share'] = None

        return CommandSearchCluster.render(self, cluster_type='esx',
                                           allowed_archetype=None,
                                           allowed_personality=None,
                                           down_hosts_threshold=None,
                                           down_maint_threshold=None,
                                           location=None, max_members=None,
                                           member_archetype=None,
                                           member_hostname=esx_hostname,
                                           member_personality=None,
                                           sandbox_author=None,
                                           **gen_arguments)
