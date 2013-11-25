# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq search system`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.list import StringAttributeList
from aquilon.aqdb.model import DnsRecord
from aquilon.worker.dbwrappers.system import search_system_query


class CommandSearchSystem(BrokerCommand):

    required_parameters = []

    def render(self, session, fullinfo, style, **arguments):
        self.deprecated_command("Command search_system is deprecated. Please "
                                "use search_hardware, search_host, or "
                                "search_dns instead.", **arguments)
        q = search_system_query(session, DnsRecord, **arguments)
        if fullinfo or style != "raw":
            return q.all()
        return StringAttributeList(q.all(), 'fqdn')
