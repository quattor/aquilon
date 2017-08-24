# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq add network_environment`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.utils import validate_nlist_key
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import NetworkEnvironment, DnsEnvironment
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddNetworkEnvironment(BrokerCommand):

    required_parameters = ["network_environment"]

    def render(self, session, network_environment, dns_environment, comments,
               user, justification, reason, logger, **arguments):
        validate_nlist_key("network environment", network_environment)
        NetworkEnvironment.get_unique(session, network_environment,
                                      preclude=True)
        dbdns_env = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)

        # Currently input.xml lists --building only, but that may change
        location = get_location(session, **arguments)

        dbnet_env = NetworkEnvironment(name=network_environment,
                                       dns_environment=dbdns_env,
                                       location=location, comments=comments)

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command)
        cm.consider(dbnet_env, enforce_validation=True)
        cm.validate()

        if dbdns_env.is_default != dbnet_env.is_default:
            raise ArgumentError("Only the default network environment may be "
                                "associated with the default DNS environment.")

        session.add(dbnet_env)
        session.flush()
        return
