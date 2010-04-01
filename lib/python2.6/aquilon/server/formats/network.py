# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Network

class NetworkFormatter(ObjectFormatter):
    protocol = "aqdnetworks_pb2"
    def format_raw(self, network, indent=""):
        netmask = network.netmask()
        sysloc = network.location.sysloc()
        details = [ indent + "Network: %s" % network.name ]
        details.append(indent + "IP: %s" % network.ip )
        details.append(indent + "Netmask: %s" % netmask)
        details.append(indent + "Sysloc: %s" % sysloc)
        details.append(indent + "Country: %s" % str(network.location.country.name))
        details.append(indent + "Side: %s" % network.side)
        details.append(indent + "Network Type: %s" % network.network_type)
        details.append(indent + "Discoverable: %s" % str(network.is_discoverable))
        details.append(indent + "Discovered: %s" % str(network.is_discovered))
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)
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
            # XXX should sort on either host or ip, output is ugly
            for system in network.interfaces:
                if hasattr(system, "fqdn"):
                    device_name = system.fqdn
                elif hasattr(system, "name"):
                    device_name = system.name
                elif hasattr(system, "machine"):
                    device_name = int.machine.name
                else:
                    device_name =  system.ip
                details.append(indent + "Host: %s Host IP: %s Host MAC: %s" % (device_name, system.ip, system.mac))
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
            details.append(indent + str("\t".join([network.name, network.ip, str(network.netmask()), network.location.sysloc(), network.location.country.name, network.side, network.network_type, str(network.is_discoverable), str(network.is_discovered), str(network.comments)])))
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
        net_msg.bcast = str(net.bcast)
        net_msg.netmask = str(net.netmask())
        net_msg.side = str(net.side)
        net_msg.sysloc = str(net.location.sysloc())
        net_msg.location.name = str(net.location.name)
        net_msg.location.location_type = str(net.location.location_type)
        net_msg.type = str(net.network_type)
        net_msg.discoverable = net.is_discoverable
        net_msg.discovered = net.is_discovered
        for system in net.interfaces:
            self.add_host_msg(net_msg.hosts.add(), system)

    def csv_fields(self, network):
        return (network.name, network.ip, network.netmask(),
                network.location.sysloc(), network.location.country.name,
                network.side, network.network_type, network.comments)

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": network.ip} for ip in shlist])

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()
