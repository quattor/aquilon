# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


from sqlalchemy.sql.expression import asc

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import System
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError
from aquilon.server.locks import lock_queue, DeleteKey


class CommandAddDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip"]

    def render(self, session, logger, startip, endip, **arguments):
        key = DeleteKey("system", logger=logger)
        try:
            lock_queue.acquire(key)
            self.del_dynamic_range(session, logger, startip, endip)
            session.commit()
        finally:
            lock_queue.release(key)
        return

    def del_dynamic_range(self, session, logger, startip, endip):
        startnet = get_net_id_from_ip(session, startip)
        endnet = get_net_id_from_ip(session, endip)
        if startnet != endnet:
            raise ArgumentError("IPs '%s' (%s) and '%s' (%s) must be on the "
                                "same subnet" %
                                (startip, startnet.ip, endip, endnet.ip))
        q = session.query(System)
        q = q.filter(System.ip >= startip)
        q = q.filter(System.ip <= endip)
        q = q.order_by(asc(System.ip))
        existing = q.all()
        if not existing:
            raise ArgumentError("Nothing found in range.")
        if existing[0].ip != startip:
            raise ArgumentError("No system found with IP address '%s'" %
                                startip)
        if existing[-1].ip != endip:
            raise ArgumentError("No system found with IP address '%s'" %
                                endip)
        invalid = [s for s in existing if s.system_type != 'dynamic_stub']
        if invalid:
            raise ArgumentError("The range contains non-dynamic systems:\n" +
                                "\n".join(["%s (%s)" % (i.fqdn, i.ip)
                                           for i in invalid]))

        for stub in existing:
            session.delete(stub)
        return
