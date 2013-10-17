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
"""Contains the logic for `aq update network_environment`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import NetworkEnvironment
from aquilon.worker.dbwrappers.location import get_location


class CommandUpdateNetworkEnvironment(BrokerCommand):

    required_parameters = ["network_environment"]

    def render(self, session, network_environment, clear_location, comments,
               **arguments):
        dbnet_env = NetworkEnvironment.get_unique(session, network_environment,
                                                  compel=True)

        # Currently input.xml lists --building only, but that may change
        location = get_location(session, **arguments)
        if location:
            dbnet_env.location = location
        if clear_location:
            dbnet_env.location = None
        if comments is not None:
            dbnet_env.comments = comments
        session.flush()
        return
