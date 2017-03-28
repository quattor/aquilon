# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
from sqlalchemy.orm import object_session, subqueryload

from aquilon.aqdb.model import Network, HardwareEntity
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
    def format_raw(self, network, indent="", embedded=True,
                   indirect_attrs=True):
        netmask = network.netmask
        sysloc = network.location.sysloc()
        details = [indent + "{0:c}: {0.name}".format(network)]
        details.append(indent + "  {0:c}: {0.name}".format(network.network_environment))
        details.append(indent + "  IP: %s" % network.ip)
        details.append(indent + "  Netmask: %s" % netmask)
        details.append(indent + "  Sysloc: %s" % sysloc)
        details.append(self.redirect_raw(network.location, indent + "  "))
        details.append(indent + "  Side: %s" % network.side)
        details.append(indent + "  Network Type: %s" % network.network_type)
        if network.network_compartment:
            details.append(indent + "  {0:c}: {0.name}".format(network.network_compartment))
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)

        if network.routers:
            routers = ", ".join(sorted("{0} ({1})".format(rtr.ip, rtr.location)
                                       for rtr in network.routers))
            details.append(indent + "  Routers: %s" % routers)

        if network.port_group:
            details.append(indent + "  Port Group: %s" %
                           network.port_group.name)

        # Look for dynamic DHCP ranges
        ranges = summarize_ranges(network.dynamic_stubs)
        if ranges:
            details.append(indent + "  Dynamic Ranges: %s" % ", ".join(ranges))

        for route in sorted(network.static_routes,
                            key=attrgetter('destination', 'gateway_ip')):
            details.append(indent + "  {0:c}: {0.destination} gateway {0.gateway_ip}"
                           .format(route))
            if route.personality_stage:
                details.append(indent + "    {0:c}: {0.name} {1:c}: {1.name}"
                               .format(route.personality_stage.personality,
                                       route.personality_stage.archetype))

                if route.personality_stage.staged:
                    details.append(indent + "      Stage: %s" %
                                   route.personality_stage.name)
            if route.comments:
                details.append(indent + "    Comments: %s" % route.comments)

        return "\n".join(details)

    def csv_fields(self, network):
        yield (network.name, network.ip, network.netmask,
               network.location.sysloc(), network.location.country,
               network.side, network.network_type, network.comments)

    def fill_proto(self, net, skeleton, embedded=True, indirect_attrs=True):
        skeleton.name = net.name
        skeleton.ip = str(net.ip)
        skeleton.cidr = net.cidr
        skeleton.bcast = str(net.broadcast)
        skeleton.netmask = str(net.netmask)
        if net.side:
            skeleton.side = net.side

        sysloc = net.location.sysloc()
        if sysloc:
            skeleton.sysloc = sysloc

        self.redirect_proto(net.location, skeleton.location,
                            indirect_attrs=False)
        skeleton.type = net.network_type
        skeleton.env_name = net.network_environment.name

        skeleton.routers.extend(str(router.ip) for router in net.routers)
        if net.network_compartment:
            skeleton.compartment = net.network_compartment.name

        # Look for dynamic DHCP ranges
        range_msg = None
        last_ip = None
        for dynhost in net.dynamic_stubs:
            if not last_ip or dynhost.ip != last_ip + 1:
                if last_ip:
                    range_msg.end = str(last_ip)
                range_msg = skeleton.dynamic_ranges.add()
                range_msg.start = str(dynhost.ip)
            last_ip = dynhost.ip
        if last_ip:
            range_msg.end = str(last_ip)

ObjectFormatter.handlers[Network] = NetworkFormatter()


class NetworkHostList(list):
    """Holds a list of networks for which a host list will be formatted
    """
    pass


class NetworkHostListFormatter(ListFormatter):
    protocol = "aqdnetworks_pb2"

    def format_raw(self, netlist, indent="", embedded=True,
                   indirect_attrs=True):
        details = []

        for network in netlist:
            # we'll get the header from the existing formatter
            nfm = NetworkFormatter()
            details.append(indent + nfm.format_raw(network))

            for addr in network.assignments:
                iface = addr.interface
                hw_ent = iface.hardware_entity
                if addr.fqdns:
                    names = ", ".join(sorted(str(fqdn) for fqdn in addr.fqdns))
                else:
                    names = "unknown"
                details.append(indent + "  {0:c}: {0.printable_name}, "
                               "interface: {1.logical_name}, "
                               "MAC: {2.mac}, IP: {1.ip} ({3})".format(
                                   hw_ent, addr, iface, names))
        return "\n".join(details)

    def format_proto(self, result, container, embedded=True, indirect_attrs=True):
        for item in result:
            skeleton = container.add()
            handler = NetworkFormatter()
            # Use the standard network formatter to fill in the non-host details
            handler.format_proto(item, skeleton, embedded=embedded,
                                 indirect_attrs=indirect_attrs)
            # Use ourself to fill in all of the assignement information
            self.fill_proto(item, skeleton, embedded=embedded,
                            indirect_attrs=indirect_attrs)

    def fill_proto(self, net, skeleton, embedded=True, indirect_attrs=True):
        # Bulk load information about anything having a network address on this
        # network
        hw_ids = set(addr.interface.hardware_entity_id for addr in
                     net.assignments)
        if hw_ids:
            session = object_session(net)
            q = session.query(HardwareEntity)
            q = q.filter(HardwareEntity.id.in_(hw_ids))
            q = q.options(subqueryload('interfaces'),
                          subqueryload('host'),
                          subqueryload('host.personality_stage'),
                          subqueryload('host.operating_system'))
            hwent_by_id = {}
            for dbhwent in q:
                hwent_by_id[dbhwent.id] = dbhwent

                iface_by_id = {}
                slaves_by_id = defaultdict(list)

                # We have all the interfaces loaded already, so compute the
                # master/slave relationships to avoid having to touch the
                # database again
                for iface in dbhwent.interfaces:
                    iface_by_id[iface.id] = iface
                    if iface.master_id is not None:
                        slaves_by_id[iface.master_id].append(iface)

                for iface in dbhwent.interfaces:
                    set_committed_value(iface, "master",
                                        iface_by_id.get(iface.master_id, None))
                    set_committed_value(iface, "slaves", slaves_by_id[iface.id])

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
                host_msg = skeleton.hosts.add()

                if addr.interface.interface_type == 'management':
                    host_msg.type = 'manager'
                else:
                    host_msg.type = hwent.hardware_type
                    if hwent.host:
                        # TODO: deprecate host_msg.archetype
                        self.redirect_proto(hwent.host.archetype,
                                            host_msg.archetype,
                                            indirect_attrs=False)
                        self.redirect_proto(hwent.host.personality_stage,
                                            host_msg.personality,
                                            indirect_attrs=False)
                        self.redirect_proto(hwent.host.operating_system,
                                            host_msg.operating_system,
                                            indirect_attrs=False)

                host_msg.hostname = addr.dns_records[0].fqdn.name
                host_msg.fqdn = str(addr.dns_records[0].fqdn)
                host_msg.dns_domain = addr.dns_records[0].fqdn.dns_domain.name

                host_msg.ip = str(addr.ip)

                if mac:
                    host_msg.mac = str(mac)

                host_msg.machine.name = hwent.label

                # aqdhcpd uses the interface list when excluding hosts it is not
                # authoritative for
                for iface in hwent.interfaces:
                    int_msg = host_msg.machine.interfaces.add()
                    int_msg.device = iface.name
                    if iface.mac:
                        int_msg.mac = str(iface.mac)


ObjectFormatter.handlers[NetworkHostList] = NetworkHostListFormatter()


class NetworkList(list):
    """By convention, holds a list of networks to be formatted as alist"""
    pass


class NetworkListFormatter(ListFormatter):
    def format_raw(self, objects, indent="", embedded=True, indirect_attrs=True):
        return "\n".join(indent + "%s/%s" % (network.ip, network.cidr)
                         for network in sorted(objects, key=attrgetter("ip")))

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join(
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": n.ip} for n in nlist)

ObjectFormatter.handlers[NetworkList] = NetworkListFormatter()


class SimpleNetworkList(list):
    """By convention, holds a list of networks to be formatted in a simple
    network map type format."""
    pass


class SimpleNetworkListFormatter(NetworkListFormatter):
    fields = ["Network", "IP", "Netmask", "Sysloc", "Country", "Side", "Network Type", "Discoverable", "Discovered", "Comments"]
    format_string = '%-16s  %-16s  %-16s  %-32s  %-8s  %-4s  %-14s  %-14s  %-14s  %s'

    def format_raw(self, nlist, indent="", embedded=True, indirect_attrs=True):
        details = [indent + self.format_string % tuple(self.fields)]
        for network in nlist:
            details.append(indent + self.format_string % (network.name,
                                                     str(network.ip),
                                                     str(network.netmask),
                                                     str(network.location.sysloc()),
                                                     str(network.location.country),
                                                     network.side,
                                                     network.network_type,
                                                     "False",
                                                     "False",
                                                     str(network.comments)))
        return "\n".join(details)

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()
