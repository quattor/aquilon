# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
""" Search the transaction log for history """

from dateutil.parser import parse
from dateutil.tz import tzutc
from sqlalchemy.sql.expression import asc, desc, or_, exists

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.transaction_info import TransactionList
from aquilon.aqdb.model import Xtn, XtnDetail, XtnEnd

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

        if keyword is not None or argument is not None:
            q = q.join(XtnDetail)
            if keyword is not None:
                q = q.filter_by(value=keyword)
            if argument is not None:
                q = q.filter_by(name=argument)
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

        return TransactionList(q.all())
