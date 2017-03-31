# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq change status`."""

from aquilon.aqdb.model import HostLifecycle
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates import TemplateDomain


class CommandChangeStatus(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["hostname"]

    def render(self, session, logger, plenaries, hostname, buildstatus, **_):
        dbhost = hostname_to_host(session, hostname)
        dbstatus = HostLifecycle.get_instance(session, buildstatus)
        changed = dbhost.status.transition(dbhost, dbstatus)

        if not changed or not dbhost.archetype.is_compileable:
            return

        session.flush()

        td = TemplateDomain(dbhost.branch, dbhost.sandbox_author, logger=logger)
        plenaries.add(dbhost, allow_incomplete=False)

        # Check to see if the resulting status is the one requested
        # and generate a message for the client if not.
        if dbhost.status != dbstatus:
            logger.client_info("Warning: requested status was '{0}' but resulting "
                               "host status is '{1}'.".
                               format (dbstatus.name, dbhost.status.name))

        # Force a host lock as pan might overwrite the profile...
        with plenaries.transaction():
            td.compile(session, only=plenaries.object_templates)

        return
