#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Host formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.net.network import Network


class NetworkFormatter(ObjectFormatter):
    protocol = "aqdnetworks_pb2"
    def format_raw(self, network, indent=""):
        netmask = network.ipcalc.netmask()
        sysloc = network.location.sysloc()
        details = [ indent + "Network: %s" % network.name ]
        details.append(indent + "IP: %s" % network.ip )
        details.append(indent + "Netmask: %s" % netmask)
        details.append(indent + "Sysloc: %s" % sysloc)
        details.append(indent + "Country: %s" % str(network.location.country.name))
        details.append(indent + "Side: %s" % network.side)
        details.append(indent + "Network Type: %s" % network.network_type)
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)
        return "\n".join(details)

    def format_proto(self, network):
        snlf = SimpleNetworkListFormatter()
        return(snlf.format_proto([network]))

ObjectFormatter.handlers[Network] = NetworkFormatter()

class NetworkHostList(list):
    """Holds a list of networks for which a host list will be formatted
    """
    pass

class NetworkHostListFormatter(ObjectFormatter):
    protocol = "aqdnetworks_pb2"
    def format_raw(self, netlist, indent=""):
        details = []
        for network in netlist:
            # we'll get the header from the existing formatter
            nfm = NetworkFormatter()
            details.append(indent + nfm.format_raw(network))
            # XXX should sort on either host or ip, output is ugly
            for iface in network.interfaces:
                for phys_iface in iface.physical_interface:
                    if phys_iface.machine.host.fqdn:
                        device_name = phys_iface.machine.host.fqdn
                    elif phys_iface.machine.host.name:
                        device_name = phys_iface.machine.host.name
                    else:
                        device_name = phys_iface.machine.name
                    details.append(indent + "Host: %s Host IP: %s Host MAC: %s" % (device_name, iface.ip, iface.mac))
        return "\n".join(details)

    def format_proto(self, netlist):
        snlf = SimpleNetworkListFormatter()
        return(snlf.format_proto(netlist))

ObjectFormatter.handlers[NetworkHostList] = NetworkHostListFormatter()

class SimpleNetworkList(list):
    """By convention, holds a list of networks to be formatted in a simple
    network map type format."""
    pass


class SimpleNetworkListFormatter(ObjectFormatter):
    protocol = "aqdnetworks_pb2"
    fields = ["Network", "IP", "Netmask", "Sysloc", "Country", "Side", "Network Type", "Comments"]
    def format_raw(self, nlist, indent=""):
        details = [indent + "\t".join(self.fields)]
        for network in nlist:
            details.append(indent + str("\t".join([network.name, network.ip, str(network.ipcalc.netmask()), network.location.sysloc(), network.location.country.name, network.side, network.network_type, str(network.comments)])))
        return "\n".join(details)

    def format_proto(self, nlist):
        netlist_msg = self.loaded_protocols[self.protocol].NetworkList()
        for n in nlist:
            self.add_net_msg(netlist_msg.networks.add(), n)
        return netlist_msg.SerializeToString()

    def add_net_msg(self, net_msg, net):
        net_msg.name = str(net.name)
        net_msg.id = net.id
        net_msg.ip = str(net.ip)
        net_msg.cidr = net.cidr
        net_msg.bcast = str(net.ipcalc.netmask())
        net_msg.mask = str(net.mask)
        net_msg.side = str(net.side)
        net_msg.sysloc = str(net.location.sysloc())
        net_msg.location.name = str(net.location.name)
        net_msg.location.location_type = str(net.location.location_type)
        for iface in net.interfaces:
            for phys_iface in iface.physical_interface:
                self.add_host_msg(net_msg.hosts.add(), phys_iface.machine.host)

    def format_csv(self, nlist):
        details = [",".join(self.fields)]
        for network in nlist:
            details.append(str(",".join([network.name, network.ip, str(network.ipcalc.netmask()), network.location.sysloc(), network.location.country.name, network.side, network.network_type, str(network.comments)])))
        return "\n".join(details)

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": network.ip} for ip in shlist])

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()


#if __name__=='__main__':
