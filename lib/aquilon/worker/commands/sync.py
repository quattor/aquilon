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
"""Contains the logic for `aq sync`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.exceptions_ import ProcessException, ArgumentError
from aquilon.aqdb.model import Domain
from aquilon.worker.processes import sync_domain


class CommandSync(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, **arguments):
        dbdomain = Domain.get_unique(session, domain, compel=True)
        if not dbdomain.tracked_branch:
            # Could check dbdomain.trackers and sync all of them...
            raise ArgumentError("sync requires a tracking domain")
        if not dbdomain.tracked_branch.is_sync_valid:
            raise ArgumentError("Tracked branch %s is set to not allow sync.  "
                                "Run aq validate to mark it as valid." %
                                dbdomain.tracked_branch.name)

        try:
            sync_domain(dbdomain, logger=logger)
        except ProcessException as e:
            raise ArgumentError("Problem encountered updating templates for "
                                "domain %s: %s", dbdomain.name, e)

        return
