# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016  Contributor
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
"""Contains the logic for `aq del domain`."""

from aquilon.exceptions_ import ArgumentError, AuthorizationException
from aquilon.aqdb.model import Domain
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import remove_branch, merge_into_trash
from aquilon.worker.dbwrappers.change_management import validate_justification


class CommandDelDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, justification, reason, user,
               requestid, **_):
        dbdomain = Domain.get_unique(session, domain, compel=True)

        # Deleting non-tracking domains may lose history, so more controls are
        # needed
        if not dbdomain.tracked_branch:
            if not dbdomain.archived:
                raise ArgumentError("{0} is not archived, it cannot be deleted."
                                    .format(dbdomain))

            if not justification:
                raise AuthorizationException("Deleting a domain may lose "
                                             "history, so --justification is "
                                             "required.")
            validate_justification(user, justification, reason)

            if self.config.has_option("broker", "trash_branch"):
                merge_msg = []
                merge_msg.append("Delete archived branch %s" % dbdomain.name)
                merge_msg.append("")
                merge_msg.append("User: %s" % user)
                merge_msg.append("Request ID: %s" % requestid)
                merge_msg.append("Justification: %s" % justification)
                if reason:
                    merge_msg.append("Reason: %s" % reason)

                merge_into_trash(self.config, logger, dbdomain.name,
                                 "\n".join(merge_msg))

        remove_branch(self.config, logger, dbdomain)
        return
