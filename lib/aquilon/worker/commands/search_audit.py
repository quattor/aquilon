# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013,2014  Contributor
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
""" Search the transaction log for history """

from dateutil.parser import parse
from dateutil.tz import tzutc

from sqlalchemy.sql.expression import asc, desc, or_, exists

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Xtn, XtnDetail, XtnEnd
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611

_IGNORED_COMMANDS = ('show_active_locks', 'show_active_commands', 'cat',
                     'search_audit')


class CommandSearchAudit(BrokerCommand):

    required_parameters = []

    def render(self, session, keyword, argument, username, command, before,
               after, return_code, limit, reverse_order, **arguments):

        q = session.query(Xtn)

        if command is not None:
            if command == 'all':
                # No filter
                pass
            elif command == 'rw':
                # Filter our command list
                q = q.filter(~Xtn.command.in_(_IGNORED_COMMANDS))
            else:
                q = q.filter_by(command=command)
        else:
            # filter out read only
            q = q.filter_by(is_readonly=False)

        if username is not None:
            username = username.lower().strip()
            q = q.filter(or_(Xtn.username == username,
                             Xtn.username.like(username + '@%')))

        # TODO: These should be typed in input.xml as datetime and use
        # the standard broker methods for dealing with input validation.
        if before is not None:
            try:
                end = parse(before)
            except ValueError:
                raise ArgumentError("Unable to parse date string '%s'" %
                                    before)
            if not end.tzinfo:
                end = end.replace(tzinfo=tzutc())
            q = q.filter(Xtn.start_time < end)

        if after is not None:
            try:
                start = parse(after)
            except ValueError:
                raise ArgumentError("Unable to parse date string '%s'" % after)
            if not start.tzinfo:
                start = start.replace(tzinfo=tzutc())
            q = q.filter(Xtn.start_time > start)

        if return_code is not None:
            if return_code == 0:
                q = q.filter(~exists().where(Xtn.xtn_id == XtnEnd.xtn_id))
            else:
                q = q.join(XtnEnd)
                q = q.filter(XtnEnd.return_code == return_code)
                q = q.reset_joinpoint()

        # FIXME: Oracle ignores indexes if it has to perform unicode -> string
        # conversion, see the discussion at:
        # https://groups.google.com/d/topic/sqlalchemy/8Xn31vBfGKU/discussion
        # We may need a more generic solution like a custom type decorator as
        # suggested in the thread, but for now str() should be enough
        if keyword is not None or argument is not None:
            q = q.join(XtnDetail)
            if keyword is not None:
                q = q.filter_by(value=str(keyword))
            if argument is not None:
                q = q.filter_by(name=str(argument))
            q = q.reset_joinpoint()

        # Set an order by when searching for the records, this controls
        # which records are selected by the limit.
        if reverse_order:
            q = q.order_by(asc(Xtn.start_time))  # N oldest records
        else:
            # default: N most recent
            q = q.order_by(desc(Xtn.start_time))

        # Limit the ordered results.
        if limit is None:
            limit = self.config.getint('broker', 'default_audit_rows')
        if limit > self.config.getint('broker', 'max_audit_rows'):
            raise ArgumentError("Cannot set the limit higher than %s" %
                                self.config.get('broker', 'max_audit_rows'))
        q = q.limit(limit)

        # Now apply the user preference to the limited output after
        # the outer joins are applied to pull in details and end information.
        if reverse_order:
            q = q.from_self().order_by(desc(Xtn.start_time))
        else:
            q = q.from_self().order_by(asc(Xtn.start_time))

        return q.all()
