# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Host formatter."""

from sqlalchemy.sql import bindparam
from sqlalchemy.orm import (contains_eager, aliased, joinedload, subqueryload,
                            lazyload)
from sqlalchemy.orm.session import object_session

from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import (Network, AddressAssignment, DnsRecord,
                                ARecord, DynamicStub,
                                PrimaryNameAssociation, DnsDomain,
                                Interface, HardwareEntity, Fqdn)

def summarize_ranges(addrlist):
    """ Convert a list like [1,2,3,5] to ["1-3", "5"], but with IP addresses """
    ranges = []
    start = None
    for addr in addrlist:
        if start is None:
            start = addr.ip
            end = addr.ip
            continue
        if int(addr.ip) == int(end) + 1:
            end = addr.ip
            continue
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append("%s-%s" % (start, end))
        start = end = addr.ip
    if start is not None:
        if start == end:
            ranges.append(str(start))
        else:
            ranges.append("%s-%s" % (start, end))

    return ranges

def possible_mac_addresses(interface):
    """ Return the list of MAC addresses the DHCP server should accept.

    There are a couple of cases to consider:

    - 801.q VLANs: the MAC address of the physical interface may appear on
      multiple networks that belong to the different VLANs configured on the
      interface.

    - Bonding devices: during PXE, the bonding is not configured yet, and the
      DHCP server should accept the MAC address of the physical interface(s).
      If the bonding device has a dedicated MAC address configured, then that
      should also be accepted if the host configures the interface using DHCP.
    """

    mac_addrs = []

    # In case of VLANs, just grab the parent interface
    if interface.interface_type == 'vlan':
        interface = interface.parent

    # Bonding/bridge: append the MACs of the physical interfaces
    # TODO: drop the public/bootable check once we decide how to send the extra
    # information to clients
    for slave in interface.all_slaves():
        if slave.mac and (slave.interface_type != "public" or slave.bootable):
            mac_addrs.append(slave.mac)

    # Handle physical interfaces, and bonding with a dedicated MAC
    # TODO: drop the public/bootable check once we decide how to send the extra
    # information to clients
    if interface.mac and (interface.interface_type != "public" or interface.bootable):
        mac_addrs.append(interface.mac)

    return mac_addrs


class NetworkFormatter(ObjectFormatter):
    protocol = "aqdnetworks_pb2"

    def format_raw(self, network, indent=""):
        netmask = network.netmask
        sysloc = network.location.sysloc()
        details = [indent + "Network: %s" % network.name]
        details.append(indent + "  {0:c}: {0.name}".format(network.network_environment))
        details.append(indent + "  IP: %s" % network.ip)
        details.append(indent + "  Netmask: %s" % netmask)
        details.append(indent + "  Sysloc: %s" % sysloc)
        details.append(indent + "  Country: %s" % str(network.location.country.name))
        details.append(indent + "  Side: %s" % network.side)
        details.append(indent + "  Network Type: %s" % network.network_type)
        details.append(indent + "  Discoverable: %s" % str(network.is_discoverable))
        details.append(indent + "  Discovered: %s" % str(network.is_discovered))
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)

        if network.routers:
            routers = ", ".join(["{0} ({1})".format(rtr.ip, rtr.location)
                                 for rtr in network.routers])
            details.append(indent + "  Routers: %s" % routers)

        # Look for dynamic DHCP ranges
        # TODO: convert it to a relation with a custom WHERE
        session = object_session(network)
        q = session.query(DynamicStub.ip)
        q = q.filter_by(network=network)
        q = q.order_by(DynamicStub.ip)
        ranges = summarize_ranges(q)
        if ranges:
            details.append(indent + "  Dynamic Ranges: %s" % ", ".join(ranges))

        return "\n".join(details)

    def format_proto(self, network, skeleton=None):
        snlf = SimpleNetworkListFormatter()
        return(snlf.format_proto([network], skeleton))

ObjectFormatter.handlers[Network] = NetworkFormatter()


class NetworkHostList(list):
    """Holds a list of networks for which a host list will be formatted
    """
    pass


class NetworkHostListFormatter(ListFormatter):
    protocol = "aqdnetworks_pb2"

    def format_raw(self, netlist, indent=""):
        details = []

        for network in netlist:
            # we'll get the header from the existing formatter
            nfm = NetworkFormatter()
            details.append(indent + nfm.format_raw(network))

            for addr in network.assignments:
                iface = addr.interface
                hw_ent = iface.hardware_entity
                if addr.fqdns:
                    names = ", ".join([str(fqdn) for fqdn in addr.fqdns])
                else:
                    names = "unknown"
                details.append(indent + "  {0:c}: {0.printable_name}, "
                               "interface: {1.logical_name}, "
                               "MAC: {2.mac}, IP: {1.ip} ({3})".format(
                                   hw_ent, addr, iface, names))
        return "\n".join(details)

    def format_proto(self, netlist, skeleton=None):
        snlf = SimpleNetworkListFormatter()
        return(snlf.format_proto(netlist, skeleton))

ObjectFormatter.handlers[NetworkHostList] = NetworkHostListFormatter()


class SimpleNetworkList(list):
    """By convention, holds a list of networks to be formatted in a simple
    network map type format."""
    pass


class SimpleNetworkListFormatter(ListFormatter):
    protocol = "aqdnetworks_pb2"
    fields = ["Network", "IP", "Netmask", "Sysloc", "Country", "Side", "Network Type", "Discoverable", "Discovered", "Comments"]

    def format_raw(self, nlist, indent=""):
        details = [indent + "\t".join(self.fields)]
        for network in nlist:
            details.append(indent + str("\t".join([network.name,
                                                   str(network.ip),
                                                   str(network.netmask),
                                                   network.location.sysloc(),
                                                   network.location.country.name,
                                                   network.side,
                                                   network.network_type,
                                                   str(network.is_discoverable),
                                                   str(network.is_discovered),
                                                   str(network.comments)])))
        return "\n".join(details)

    def format_proto(self, nlist, skeleton=None):
        netlist_msg = self.loaded_protocols[self.protocol].NetworkList()
        for n in nlist:
            self.add_net_msg(netlist_msg.networks.add(), n)
        return netlist_msg.SerializeToString()

    def add_net_msg(self, net_msg, net):
        net_msg.name = str(net.name)
        net_msg.id = net.id
        net_msg.ip = str(net.ip)
        net_msg.cidr = net.cidr
        net_msg.bcast = str(net.broadcast)
        net_msg.netmask = str(net.netmask)
        net_msg.side = str(net.side)
        net_msg.sysloc = str(net.location.sysloc())
        net_msg.location.name = str(net.location.name)
        net_msg.location.location_type = str(net.location.location_type)
        net_msg.type = str(net.network_type)
        net_msg.discoverable = net.is_discoverable
        net_msg.discovered = net.is_discovered

        # Add interfaces that have addresses in this network
        for addr in net.assignments:
            hwent = addr.interface.hardware_entity

            if not addr.dns_records:
                # hostname is a required field in the protobuf description
                continue

            # DHCP: we do not care about secondary IP addresses, but in some
            # cases the same IP address may show up with different MACs
            if not addr.label:
                mac_addrs = possible_mac_addresses(addr.interface)
            else:
                mac_addrs = []

            # Generate a host record even if there is no known MAC address for
            # it
            if not mac_addrs:
                mac_addrs.append(None)

            # Associating the same IP with multiple MAC addresses is
            # problematic using the current protocol. Sending multiple host
            # messages is easy for the broker, but it can confuse consumers like
            # aqdhcpd. For now just ensure it never happens, and revisit the
            # problem when we have a real world requirement.
            if len(mac_addrs) > 1:
                mac_addrs = [mac_addrs[0]]

            for mac in mac_addrs:
                host_msg = net_msg.hosts.add()

                if addr.interface.interface_type == 'management':
                    host_msg.type = 'manager'
                else:
                    if hwent.hardware_type == 'machine':
                        host_msg.type = 'host'
                        if hwent.host:
                            host_msg.archetype.name = str(hwent.host.archetype.name)
                    elif hwent.hardware_type == 'switch':
                        # aqdhcpd uses the type
                        host_msg.type = 'tor_switch'
                    else:
                        host_msg.type = hwent.hardware_type

                host_msg.hostname = str(addr.dns_records[0].fqdn.name)
                host_msg.fqdn = str(addr.dns_records[0].fqdn)
                host_msg.dns_domain = str(addr.dns_records[0].fqdn.dns_domain)

                host_msg.ip = str(addr.ip)

                if mac:
                    host_msg.mac = mac

                host_msg.machine.name = str(hwent.label)

                # aqdhcpd uses the interface list when excluding hosts it is not
                # authoritative for
                for iface in hwent.interfaces:
                    int_msg = host_msg.machine.interfaces.add()
                    int_msg.device = iface.name
                    if iface.mac:
                        int_msg.mac = str(iface.mac)

        # Add dynamic DHCP records
        # TODO: convert it to a relation with a custom WHERE
        session = object_session(net)
        q = session.query(DynamicStub)
        q = q.filter_by(network=net)
        for dynhost in q:
            host_msg = net_msg.hosts.add()
            # aqdhcpd uses the type
            host_msg.type = 'dynamic_stub'
            host_msg.hostname = str(dynhost.fqdn.name)
            host_msg.fqdn = str(dynhost.fqdn)
            host_msg.dns_domain = str(dynhost.fqdn.dns_domain)
            host_msg.ip = str(dynhost.ip)

    def csv_fields(self, network):
        return (network.name, network.ip, network.netmask,
                network.location.sysloc(), network.location.country.name,
                network.side, network.network_type, network.comments)

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": n.ip} for n in nlist])

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()


class ShortNetworkList(list):
    """By convention, holds a list of networks to be formatted.

    The format is just the IP and mask.

    """
    pass


class ShortNetworkListFormatter(SimpleNetworkListFormatter):

    def format_raw(self, nlist, indent=""):
        return "\n".join(["%s/%s" % (n.ip, n.cidr) for n in nlist])

ObjectFormatter.handlers[ShortNetworkList] = ShortNetworkListFormatter()
