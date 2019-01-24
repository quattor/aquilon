# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011-2018  Contributor
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

from datetime import datetime
from datetime import timedelta
from dateutil.parser import parse
from dateutil.tz import tzutc

from sqlalchemy.sql.expression import asc, desc, exists
from sqlalchemy import or_

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Xtn, XtnDetail, XtnEnd
from aquilon.worker.broker import BrokerCommand

_IGNORED_COMMANDS = ('show_active_locks', 'show_active_commands', 'cat',
                     'search_audit')

_NON_DB_CHANGE_TYPE_COMMANDS = ('compile', 'pxeswitch')


class CommandSearchAudit(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, keyword, argument, username, command,
               before, after, forever, return_code, limit, reverse_order, **_):
        """Render the search_audit command.

        Please see the abstract method defined in the superclass of this
        class to better understand the purpose of the render method.

        :param keyword: The value of any argument supplied to a command
                        (str or None)
        :param argument: Look at the value of the specified argument only
                         (str or None)
        :param username: The user name who executed the command
                         (str or None)
        :param command: The name of the command or command type
                        (str or None)
        :param before: Search for transactions started before a specific
                       date/time (str or None)
        :param after: Search for transactions started after a specific
                      date/time (str or None)
        :param forever: Search for transactions throughout the transaction log
                        (a flag, any value that evaluates to True or False)
        :param return_code: Search by an HTTP response code (None or
                            int: 200-505)
        :param limit: Limit the number of rows returned. (None (sets limit
                      to the configured default value) or int))
        :param reverse_order: Output records in reverse chronological order.
                              Also causes the --limit parameter to find the
                              oldest records and not the newest.
                              (a flag, any value that evaluates to True or
                              False)

        :return: a list of all results represented by the computed SQLAlchemy
                 Query object
        """
        q = session.query(Xtn)

        if command is not None:
            if command == 'all':
                # No filter
                pass
            elif command == 'rw':
                # Filter our command list
                q = q.filter(~Xtn.command.in_(_IGNORED_COMMANDS))
            elif command == 'wo':
                # Filter command list to only return manipulate commands to db
                # Old default behaviour
                q = q.filter_by(is_readonly=False)
            elif command == 'ro':
                # Filter our command list to only return readonly commands
                q = q.filter_by(is_readonly=True)
            else:
                q = q.filter_by(command=str(command))
        else:
            # filter out read only
            q = q.filter(or_(Xtn.is_readonly == False,
                             Xtn.command.in_(_NON_DB_CHANGE_TYPE_COMMANDS)))

        if username is not None:
            username = username.strip()
            # 'nobody' is special, it is stored without any realm
            if '@' in username or username == 'nobody':
                q = q.filter_by(username=str(username))
            else:
                q = q.filter(Xtn.username.like(username + '@%'))

        # TODO: These should be typed in input.xml as datetime and use
        # the standard broker methods for dealing with input validation.
        start, end = self.after_before_to_start_end(after, before)

        if forever:
            if before is not None or after is not None:
                raise ArgumentError(
                    "Cannot specify 'forever' with 'before' or 'after'")
        else:
            # if no end-time set, and no start time set, use now;  if
            # start-time if set (and no end), end at +1 year.  (unless
            # 'forever' is given)

            if end is None:
                if start is None:
                    # Note: put this 1s in the future so we don't accidently
                    # miss things that were added within the last second (from
                    # zero'd microseconds).
                    end = datetime.utcnow().replace(microsecond=0) +\
                          timedelta(seconds=1)
                else:
                    end = start + timedelta(days=366)

                if not end.tzinfo:
                    end = end.replace(tzinfo=tzutc())

            if start is None:
                start = end - timedelta(days=366)
                if not start.tzinfo:
                    start = start.replace(tzinfo=tzutc())

            # sanity check: that end is after before.
            if end < start:
                raise ArgumentError(
                    "Time region from after '{}' to before '{}'"
                    " is invalid.".format(after, before))

            q = q.filter(Xtn.start_time > start, Xtn.start_time < end)

        if return_code is not None:
            if return_code == 0:
                q = q.filter(~exists().where(Xtn.id == XtnEnd.xtn_id))
            else:
                q = q.join(XtnEnd)
                q = q.filter(XtnEnd.return_code == return_code)
                q = q.reset_joinpoint()

        # FIXME: Oracle ignores indices if it has to perform unicode -> string
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
            raise ArgumentError(
                "Cannot set the limit higher than {}".format(
                    self.config.get('broker', 'max_audit_rows')))
        q = q.limit(limit)

        # Now apply the user preference to the limited output after
        # the outer joins are applied to pull in details and end information.
        if reverse_order:
            q = q.from_self().order_by(desc(Xtn.start_time))
        else:
            q = q.from_self().order_by(asc(Xtn.start_time))

        return q.all()

    @classmethod
    def after_before_to_start_end(cls, after, before):
        """Return a tuple (start, end) with parsed 'after' and 'before'.

        This method parses after and before and returns a tuple (start, end)
        specifying a period of interest, where each item is either a None (if
        initially None) or a datetime object.
        NB: This method purposefully does not ensure that start < end (this is
        done elsewhere).

        :param after: None, datetime or str
        :param before: None, datetime or str

        :return: a tuple (start, end) - each item is either set to None, or an
                 instance of datetime (with UTC timezone if no other timezone
                 given).
        """
        # To protect ourselves against some very unlikely cases when 'after'
        # would be erroneously computed to precede 'before' (for different
        # combinations of 'now' or 'today' (NB: if today is used for either
        # of the parameters, using now or today for another one does not
        # make sense)), and to ensure that, from the user perspective, 'now'
        # means 'now', we must use the same value of 'now' and 'tzinfo' (in
        # this case we only use UTC) for both.
        now = datetime.now()
        tzinfo = tzutc()
        if after == 'today':
            after = now.combine(now.date(), now.max.time())
        if before == 'today':
            before = now.combine(now.date(), now.min.time())
        after = cls._parsed_datetime_or_none(after, now, tzinfo)
        before = cls._parsed_datetime_or_none(before, now, tzinfo)
        return after, before

    @staticmethod
    def _parsed_datetime_or_none(fuzzy_dt, now=None, tzinfo=None):
        """Parse fuzzy_dt and return a datetime object on success, or None."""
        if fuzzy_dt is None:
            return None
        if fuzzy_dt == 'now':
            parsed = now or datetime.now()
        elif isinstance(fuzzy_dt, datetime):
            parsed = fuzzy_dt
        else:
            try:
                parsed = parse(fuzzy_dt)
            except (ValueError, TypeError):
                raise ArgumentError(
                    "Unable to parse date string '{}'".format(fuzzy_dt))
        if parsed.tzinfo is None:
            parsed = parsed.replace(tzinfo=tzinfo or tzutc())
        return parsed
