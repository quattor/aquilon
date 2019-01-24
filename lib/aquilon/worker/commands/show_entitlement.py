# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2018  Contributor
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
"""Contains the logic for `aq show_entitlement`."""

from aquilon.aqdb.model import Host
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.entitlement import (
    get_entitlements_options,
    get_host_entitlements,
)


class CommandShowEntitlement(BrokerCommand):

    def render(self, session, logger, **arguments):
        # Parse the options to get the entitlements options
        dbtos, dbon, dblocations, dbenvs, dbtype = get_entitlements_options(
            session=session, logger=logger, config=self.config,
            on_single=True, **arguments)

        # If no host was provided, raise an exception
        if not dbon:
            raise ArgumentError('No target provided')

        # If the element provided is not a host, raise an exception
        if not isinstance(dbon, Host):
            raise ArgumentError('show_entitlement only works on Host objects')

        # If a location is provided, raise an exception; this should never
        # happen as it should be blocked at the request level
        if dblocations:
            raise ArgumentError('show_entitlement does not support location '
                                'options')

        # If an environment is provided, raise an exception; this should never
        # happen as it should be blocked at the request level
        if dbenvs:
            raise ArgumentError('show_entitlement does not support '
                                'environment options')

        # Pass the arguments to the wrapper function that will do the job
        # for us
        query = get_host_entitlements(dbon, dbtype=dbtype, dbtos=dbtos)

        # Return query results
        return query.all()
