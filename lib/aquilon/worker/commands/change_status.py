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
"""Contains the logic for `aq change status`."""

from aquilon.aqdb.model import HostLifecycle
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates import Plenary, PlenaryCollection, TemplateDomain


class CommandChangeStatus(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, buildstatus, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbstatus = HostLifecycle.get_instance(session, buildstatus)
        changed = dbhost.status.transition(dbhost, dbstatus)

        if not changed or not dbhost.archetype.is_compileable:
            return

        session.flush()

        td = TemplateDomain(dbhost.branch, dbhost.sandbox_author, logger=logger)
        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbhost, allow_incomplete=False))

        # Force a host lock as pan might overwrite the profile...
        with plenaries.get_key():
            plenaries.stash()
            try:
                plenaries.write(locked=True)
                td.compile(session, only=plenaries.object_templates, locked=True)
            except:
                plenaries.restore_stash()
                raise
        return
