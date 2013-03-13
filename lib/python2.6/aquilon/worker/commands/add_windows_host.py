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
"""Contains a wrapper for `aq add windows host`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_host import CommandAddHost


class CommandAddWindowsHost(CommandAddHost):

    required_parameters = ["hostname", "machine"]

    def render(self, *args, **kwargs):
        kwargs['archetype'] = 'windows'
        kwargs['osname'] = 'windows'
        kwargs['domain'] = None
        kwargs['sandbox'] = None
        kwargs['zebra_interfaces'] = None
        # The superclass already contains the logic to handle this case.
        return CommandAddHost.render(self, *args, **kwargs)
