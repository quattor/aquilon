# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
from sqlalchemy.sql.expression import asc, desc, or_, exists

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.formats.transaction_info import TransactionList
from aquilon.aqdb.model import Xtn, XtnDetail, XtnEnd

_IGNORED_COMMANDS = ('show_active_locks','show_active_commands', 'cat',
                     'search_audit')


class CommandSearchAudit(BrokerCommand):

    required_parameters = []

    def render(self, session, logger, keyword, username, cmd, before, after,
               return_code, limit, oldest_first, **arguments):

        q = session.query(Xtn)

        if cmd is not None:
            if cmd == 'all':
                # No filter
                pass
            elif cmd == 'rw':
                # Filter our command list
                q = q.filter(~Xtn.command.in_(_IGNORED_COMMANDS))
            else:
                q = q.filter_by(command=cmd)
        else:
            # filter out read only
            q = q.filter_by(is_readonly=False)

        if username is not None:
            username = username.lower().strip()
            q = q.filter(or_(Xtn.username==username,
                             Xtn.username.like(username + '@%')))

        if before is not None:
            try:
                end = parse(before)
            except ValueError:
                raise ArgumentError("Unable to parse date string '%s'" %
                                    before)
            q = q.filter(Xtn.start_time < end)

        if after is not None:
            try:
                start = parse(after)
            except ValueError:
                raise ArgumentError("Unable to parse date string '%s'" % after)
            q = q.filter(Xtn.start_time > start)

        if return_code is not None:
            if return_code == 0:
                q = q.filter(~exists().where(Xtn.xtn_id == XtnEnd.xtn_id))
            else:
                q = q.join(XtnEnd)
                q = q.filter(XtnEnd.return_code==return_code)
                q = q.reset_joinpoint()

        if keyword is not None:
            q = q.join(XtnDetail).filter_by(value=keyword)
            q = q.reset_joinpoint()

        # Set an order by when searching for the records.
        if oldest_first:
            q = q.order_by(asc(Xtn.start_time))
        else:
            q = q.order_by(desc(Xtn.start_time))

        # Limit the ordered results.
        if limit is None:
            limit = self.config.getint('broker', 'default_audit_rows')
        if limit > self.config.getint('broker', 'max_audit_rows'):
            raise ArgumentError("Cannot set the limit higher than %s" %
                                self.config.get('broker', 'max_audit_rows'))
        q = q.limit(limit)

        # Now make sure the limited output is ordered after the outer joins
        # are applied to pull in details and end information.
        if oldest_first:
            q = q.from_self().order_by(asc(Xtn.start_time))
        else:
            q = q.from_self().order_by(desc(Xtn.start_time))

        return TransactionList(q.all())
