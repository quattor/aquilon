# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011,2012  Contributor
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

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.commands.del_dynamic_range import CommandDelDynamicRange
from aquilon.aqdb.model import DynamicStub, Network, NetworkEnvironment
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.locks import DeleteKey


class CommandDelDynamicRangeClearnetwork(CommandDelDynamicRange):

    required_parameters = ["clearnetwork"]

    def render(self, session, logger, clearnetwork, **arguments):
        with DeleteKey("system", logger=logger) as key:
            self.del_dynamic_network(session, logger, clearnetwork)
            session.commit()
        return

    def del_dynamic_network(self, session, logger, network):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        dbnetwork = Network.get_unique(session, network,
                                       network_environment=dbnet_env,
                                       compel=True)
        q = session.query(DynamicStub)
        q = q.filter_by(network=dbnetwork)
        q = q.order_by(asc(DynamicStub.ip))
        existing = q.all()
        if not existing:
            raise ArgumentError("No dynamic stubs found on network.")
        self.del_dynamic_stubs(session, logger, existing)
