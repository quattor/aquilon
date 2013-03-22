# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains a wrapper for `aq del windows host`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_host import CommandDelHost
from aquilon.worker.dbwrappers.host import hostname_to_host


class CommandDelWindowsHost(CommandDelHost):

    required_parameters = ["hostname"]

    def render(self, *args, **kwargs):
        session = kwargs['session']
        hostname = kwargs['hostname']
        dbhost = hostname_to_host(session, hostname)
        if dbhost.archetype.name != 'windows':
            raise ArgumentError("Host %s has archetype %s, expected windows." %
                                (dbhost.fqdn, dbhost.archetype.name))
        # The superclass already contains the logic to handle this case.
        return CommandDelHost.render(self, *args, **kwargs)
