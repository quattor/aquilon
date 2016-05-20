# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2015  Contributor
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
"""Contains the logic for `aq show host --hostname`."""

from sqlalchemy.orm import undefer, joinedload

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandShowHostHostname(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, **_):
        # hostname_to_host() runs a query for HardwareEntity, so options should
        # be relative to that
        options = [undefer('comments'),
                   joinedload('host'),
                   undefer('host.comments'),
                   undefer('host.personality_stage.personality.comments'),
                   undefer('host.personality_stage.personality.archetype.comments'),
                   joinedload('model'),
                   joinedload('model.vendor')]
        return hostname_to_host(session, hostname, query_options=options)
