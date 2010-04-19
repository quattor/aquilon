# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010  Contributor
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
"""Contains the logic for `aq search network`."""


from aquilon.server.broker import BrokerCommand
from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Network, Machine, VlanInfo, ObservedVlan,
                                Cluster)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.formats.network import ShortNetworkList
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandSearchNetwork(BrokerCommand):

    required_parameters = []

    def render(self, session, network, ip, type, discoverable, discovered,
               machine, fqdn, cluster, pg, fullinfo, **arguments):
        """Return a network matching the parameters.

        Some of the search terms can only return a unique network.  For
        those (like ip and fqdn) we proceed with the query anyway.  This
        allows for quick scripted tests like "is the network for X.X.X.X
        a tor_net2?".

        """
        q = session.query(Network)
        if network:
            q = q.filter_by(name=network)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)
            q = q.filter_by(id=dbnetwork.id)
        if type:
            q = q.filter_by(network_type=type)
        if discoverable is not None:
            q = q.filter_by(is_discoverable=discoverable)
        if discovered is not None:
            q = q.filter_by(is_discovered=discovered)
        if machine:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            vlans = []
            if dbmachine.cluster and dbmachine.cluster.switch:
                # If this is a VM on a cluster, consult the VLANs.  There
                # could be functionality here for real hardware to consult
                # interface port groups... there's no real use case yet.
                vlans = [VlanInfo.get_vlan_id(session, i.port_group)
                         for i in dbmachine.interfaces if i.port_group]
                if vlans:
                    q = q.join(['observed_vlans'])
                    q = q.filter_by(switch=dbmachine.cluster.switch)
                    q = q.filter(ObservedVlan.vlan_id.in_(vlans))
                    q = q.reset_joinpoint()
            if not vlans:
                networks = [i.system.network.id for i in dbmachine.interfaces
                            if i.system and i.system.network]
                if not networks:
                    msg = "{0} has no interfaces ".format(dbmachine)
                    if dbmachine.cluster:
                        msg += "with a portgroup or "
                    msg += "assigned to a network."
                    raise ArgumentError(msg)
                q = q.filter(Network.id.in_(networks))
        if fqdn:
            dbsystem = get_system(session, fqdn)
            q = q.filter_by(id=dbsystem.network.id)
        if cluster:
            dbcluster = Cluster.get_unique(session, cluster, compel=True)
            if dbcluster.switch:
                q = q.join(['observed_vlans'])
                q = q.filter_by(switch=dbcluster.switch)
                q = q.reset_joinpoint()
            else:
                net_ids = [h.network.id for h in dbcluster.hosts if h.network]
                q = q.filter(Network.id.in_(net_ids))
        if pg:
            vlan = VlanInfo.get_vlan_id(session, pg, compel=ArgumentError)
            q = q.join(['observed_vlans'])
            q = q.filter_by(vlan_id=vlan)
            q = q.reset_joinpoint()
        dblocation = get_location(session, **arguments)
        if dblocation:
            if arguments.get('exact_location'):
                q = q.filter_by(location=dblocation)
            else:
                childids = dblocation.offspring_ids()
                q = q.filter(Network.location_id.in_(childids))
        q = q.order_by(Network.ip)
        if fullinfo:
            return q.all()
        return ShortNetworkList(q.all())
