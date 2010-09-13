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
"""Contains the logic for `aq del switch`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Switch
from aquilon.server.broker import BrokerCommand
from aquilon.server.processes import DSDBRunner
from aquilon.server.locks import lock_queue, DeleteKey


class CommandDelSwitch(BrokerCommand):

    required_parameters = ["switch"]

    def render(self, session, logger, switch, **arguments):
        dbswitch = Switch.get_unique(session, switch, compel=True)
        key = DeleteKey("system", logger=logger)
        try:
            lock_queue.acquire(key)
            self.del_switch(session, logger, dbswitch)
            session.commit()
        finally:
            lock_queue.release(key)
        return

    def del_switch(self, session, logger, dbswitch):
        dbdns_rec = dbswitch.primary_name
        session.delete(dbswitch)
        if dbdns_rec:
            ip = dbdns_rec.ip
            session.delete(dbdns_rec)
        else:
            ip = None

        session.flush()

        # Any switch ports hanging off this switch should be deleted with
        # the cascade delete of the switch.

        if ip:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.delete_host_details(ip)
            except ProcessException, e:
                raise ArgumentError("Could not remove switch from DSDB: %s" %
                                    e)
        return
