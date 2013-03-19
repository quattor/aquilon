# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq show network`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Network, NetworkEnvironment
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.worker.formats.network import SimpleNetworkList
from aquilon.worker.formats.network import NetworkHostList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, network_environment, all, style,
               type=False, hosts=False, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        dbnetwork = network and get_network_byname(session, network, dbnet_env) or None
        dbnetwork = ip and get_network_byip(session, ip, dbnet_env) or dbnetwork
        q = session.query(Network)
        q = q.filter_by(network_environment=dbnet_env)
        q = q.options(joinedload('location'))
        if dbnetwork:
            if hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork
        if type:
            q = q.filter_by(network_type=type)
        dblocation = get_location(session, **arguments)
        if dblocation:
            childids = dblocation.offspring_ids()
            q = q.filter(Network.location_id.in_(childids))
        q = q.order_by(Network.ip)
        if hosts or style == "proto":
            q = q.options(subqueryload("assignments"))
            q = q.options(joinedload("assignments.dns_records"))
            q = q.options(subqueryload("dynamic_stubs"))
        if hosts:
            return NetworkHostList(q.all())
        else:
            return SimpleNetworkList(q.all())
