# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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
"""Contains the logic for `aq show active commands`."""


import re
from logging import DEBUG, INFO

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.messages import StatusCatalog


class CommandShowActiveCommands(BrokerCommand):

    requires_transaction = False
    requires_azcheck = False
    defer_to_thread = False

    incoming_re = re.compile(r'Incoming command #(?P<id>\d+)'
                             r' from user=(?P<user>\S+)'
                             r' aq (?P<command>\S+)'
                             r' with arguments {(?P<bareargs>.*)}')

    def render(self, debug, **arguments):
        catalog = StatusCatalog()
        retval = []
        if debug:
            loglevel = DEBUG
        else:
            # Note this is server level info!  That's more than the client
            # normally gets...
            loglevel = INFO
        # These could be streamed like show_request...
        for auditid in sorted(catalog.status_by_auditid.keys(), key=int):
            status = catalog.get_request_status(auditid=auditid)
            if not status:
                continue
            if status.is_finished:
                continue
            retval.append(status.description)
            for record in status.records:
                # While reading status.records directly, need to be careful
                # of any that have been removed.
                if not record:
                    continue
                if record.levelno >= loglevel:
                    message = record.getMessage()
                    if self.incoming_re.match(message):
                        # The Incoming command message is highly redundant with
                        # the status description that's already been printed.
                        continue
                    retval.append('(%s) %s' % (auditid, message))
        return str("\n".join(retval))
