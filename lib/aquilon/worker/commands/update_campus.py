# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2015  Contributor
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
"""Contains the logic for `aq update campus`."""

from aquilon.aqdb.model import Campus
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import update_location


class CommandUpdateCampus(BrokerCommand):

    required_parameters = ["campus"]

    def render(self, session, campus, fullname, default_dns_domain, comments,
               **arguments):
        dbcampus = Campus.get_unique(session, campus, compel=True)

        update_location(dbcampus, default_dns_domain=default_dns_domain,
                        fullname=fullname, comments=comments)

        session.flush()

        # TODO: update DSDB?

        return
