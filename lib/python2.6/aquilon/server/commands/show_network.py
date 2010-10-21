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
"""Contains the logic for `aq show network`."""

from sqlalchemy.orm import (joinedload, subqueryload_all, subqueryload,
                            lazyload, contains_eager)

from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Interface, Network
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.network import get_network_byname, get_network_byip
from aquilon.server.formats.network import SimpleNetworkList
from aquilon.server.formats.network import NetworkHostList


class CommandShowNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, all, discovered, discoverable,
               type=None, hosts=False, **arguments):
        dbnetwork = network and get_network_byname(session, network) or None
        dbnetwork = ip and get_network_byip(session, ip) or dbnetwork
        if dbnetwork:
            if hosts:
                return NetworkHostList([dbnetwork])
            else:
                return dbnetwork

        q = session.query(Network)
        if network:
            q = q.filter_by(name=network)
        if ip:
            q = q.filter_by(ip=ip)
        if type:
            q = q.filter_by(network_type=type)
        if discoverable is not None:
            q = q.filter_by(is_discoverable=discoverable)
        if discovered is not None:
            q = q.filter_by(is_discovered=discovered)
        dblocation = get_location(session, **arguments)
        if dblocation:
            childids = dblocation.offspring_ids()
            q = q.filter(Network.location_id.in_(childids))
        q = q.options(subqueryload('dynamic_addresses'))
        q = q.options(joinedload('dynamic_addresses.dns_domain', innerjoin=True))

        # XXX These are only neccessary if either --hosts or --format=proto was
        # specified; but how to test for --format=proto here?
        q = q.options(subqueryload_all('assignments.dns_records'))
        q = q.options(joinedload('assignments.dns_records.dns_domain'))
        q = q.options(joinedload('assignments.vlan', innerjoin=True))
        q = q.options(joinedload('assignments.vlan.interface', innerjoin=True))
        q = q.options(joinedload('assignments.vlan.interface.hardware_entity',
                                 innerjoin=True))
        q = q.options(joinedload('assignments.vlan.interface.hardware_entity.'
                                 '_primary_name_asc'))
        q = q.options(joinedload('assignments.vlan.interface.hardware_entity.'
                                 '_primary_name_asc.dns_record'))
        q = q.options(subqueryload('assignments.vlan.interface.hardware_entity.'
                                   'interfaces'))
        q = q.options(lazyload('assignments.vlan.interface.hardware_entity.'
                               'interfaces.hardware_entity'))
        q = q.options(joinedload('assignments.vlan.interface.hardware_entity.'
                                 'host.personality'))
        q = q.options(joinedload('assignments.vlan.interface.hardware_entity.'
                                 'host.personality.archetype'))

        q = q.order_by(Network.ip)

        nets = q.all()

        if hosts:
            return NetworkHostList(nets)
        else:
            return SimpleNetworkList(nets)
