# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016 Contributor
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
""" Contains the logic for `aq del cluster systemlist --all`. """

from aquilon.aqdb.model import SystemList
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_resource import CommandDelResource


class CommandDelClusterSystemListAll(CommandDelResource):

    required_parameters = ["cluster", "all"]
    resource_class = SystemList

    def render(self, all, **kwargs):  # pylint: disable=W0613
        super(CommandDelClusterSystemListAll, self).render(hostname=None,
                                                           metacluster=None,
                                                           **kwargs)
