# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Network formatter."""

from collections import defaultdict
from operator import attrgetter

from sqlalchemy.orm.attributes import set_committed_value
from sqlalchemy.orm import object_session, subqueryload, lazyload

from aquilon.aqdb.model import Network, HardwareEntity, Host
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter


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
    def format_raw(self, network, indent=""):
        netmask = network.netmask
        sysloc = network.location.sysloc()
        details = [indent + "Network: %s" % network.name]
        details.append(indent + "  {0:c}: {0.name}".format(network.network_environment))
        details.append(indent + "  IP: %s" % network.ip)
        details.append(indent + "  Netmask: %s" % netmask)
        details.append(indent + "  Sysloc: %s" % sysloc)
        details.append(self.redirect_raw(network.location, indent + "  "))
        details.append(indent + "  Side: %s" % network.side)
        details.append(indent + "  Network Type: %s" % network.network_type)
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)

        if network.routers:
            routers = ", ".join(["{0} ({1})".format(rtr.ip, rtr.location)
                                 for rtr in network.routers])
            details.append(indent + "  Routers: %s" % routers)

        # Look for dynamic DHCP ranges
        ranges = summarize_ranges(network.dynamic_stubs)
        if ranges:
            details.append(indent + "  Dynamic Ranges: %s" % ", ".join(ranges))

        for route in sorted(network.static_routes,
                            key=attrgetter('destination', 'gateway_ip')):
            details.append(indent + "  Static Route: %s gateway %s" %
                           (route.destination, route.gateway_ip))
            if route.personality:
                details.append(indent + "    Personality: {0}".format(route.personality))
            if route.comments:
                details.append(indent + "    Comments: %s" % route.comments)

        return "\n".join(details)

    def csv_fields(self, network):
        yield (network.name, network.ip, network.netmask,
               network.location.sysloc(), network.location.country,
               network.side, network.network_type, network.comments)

    def add_net_data(self, net_msg, net):
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

        # Bulk load information about anything having a network address on this
        # network
        hw_ids = set([addr.interface.hardware_entity_id for addr in
                      net.assignments])
        if hw_ids:
            session = object_session(net)
            q = session.query(HardwareEntity)
            q = q.filter(HardwareEntity.id.in_(hw_ids))
            q = q.options(subqueryload('interfaces'),
                          lazyload('interfaces.hardware_entity'))
            hwent_by_id = {}
            for dbhwent in q.all():
                hwent_by_id[dbhwent.id] = dbhwent

                iface_by_id = {}
                slaves_by_id = defaultdict(list)

                # We have all the interfaces loaded already, so compute the
                # master/slave relationships to avoid having to touch the
                # database again
                for iface in dbhwent.interfaces:
                    iface_by_id[iface.id] = iface
                    if iface.master_id:
                        slaves_by_id[iface.master_id].append(iface)

                for iface in dbhwent.interfaces:
                    set_committed_value(iface, "master",
                                        iface_by_id.get(iface.master_id, None))
                    set_committed_value(iface, "slaves", slaves_by_id[iface.id])

            # TODO: once we refactor Host to be an FK to HardwareEntity instead
            # of Machine, this could be converted to a single joinedload('host')
            q = session.query(Host)
            q = q.options(lazyload('hardware_entity'))
            q = q.filter(Host.hardware_entity_id.in_(hw_ids))
            for host in q.all():
                set_committed_value(hwent_by_id[host.hardware_entity_id], "host", host)
                set_committed_value(host, "hardware_entity",
                                    hwent_by_id[host.hardware_entity_id])

        # Add interfaces that have addresses in this network
        for addr in net.assignments:
            if not addr.dns_records:
                # hostname is a required field in the protobuf description
                continue

            hwent = addr.interface.hardware_entity

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
                    host_msg.mac = str(mac)

                host_msg.machine.name = str(hwent.label)

                # aqdhcpd uses the interface list when excluding hosts it is not
                # authoritative for
                for iface in hwent.interfaces:
                    int_msg = host_msg.machine.interfaces.add()
                    int_msg.device = iface.name
                    if iface.mac:
                        int_msg.mac = str(iface.mac)

        # Add dynamic DHCP records
        for dynhost in net.dynamic_stubs:
            host_msg = net_msg.hosts.add()
            # aqdhcpd uses the type
            host_msg.type = 'dynamic_stub'
            host_msg.hostname = str(dynhost.fqdn.name)
            host_msg.fqdn = str(dynhost.fqdn)
            host_msg.dns_domain = str(dynhost.fqdn.dns_domain)
            host_msg.ip = str(dynhost.ip)

    def format_proto(self, network, container):
        skeleton = container.networks.add()
        self.add_net_data(skeleton, network)

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
                                                   str(network.location.sysloc()),
                                                   str(network.location.country),
                                                   network.side,
                                                   network.network_type,
                                                   "False",
                                                   "False",
                                                   str(network.comments)])))
        return "\n".join(details)

    def csv_fields(self, network):
        yield (network.name, network.ip, network.netmask,
               network.location.sysloc(), network.location.country,
               network.side, network.network_type, network.comments)

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": n.ip} for n in nlist])

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()
