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
    def format_raw(self, network, indent=""):
        netmask = network.ipcalc.netmask()
        sysloc = network.location.sysloc()
        network_type = network.type.name()
        details = [ indent + "Network: %s" % network.name ]
        details.append(indent + "IP: %s" % network.ip )
        details.append(indent + "Netmask: %s" % netmask)
        details.append(indent + "Sysloc: %s" % sysloc)
        details.append(indent + "Country: %s" % str(network.location.country.name))
        details.append(indent + "Side: %s" % network.side)
        details.append(indent + "Network Type: %s" % network.type.name())
        if network.comments:
            details.append(indent + "  Comments: %s" % network.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Network] = NetworkFormatter()


class SimpleNetworkList(list):
    """By convention, holds a list of hosts to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleNetworkListFormatter(ObjectFormatter):
    fields = ["Network", "IP", "Netmask", "Sysloc", "Country", "Side", "Network Type", "Comments"]
    def format_raw(self, nlist, indent=""):
        details = [indent + "\t".join(self.fields)]
        for network in nlist:
            details.append(indent + str("\t".join([network.name, network.ip, str(network.ipcalc.netmask()), network.location.sysloc(), network.location.country.name, network.side, network.type.name(), str(network.comments)])))
        return "\n".join(details)

    def format_csv(self, nlist):
        details = [",".join(self.fields)]
        for network in nlist:
            details.append(str(",".join([network.name, network.ip, str(network.ipcalc.netmask()), network.location.sysloc(), network.location.country.name, network.side, network.type.name(), str(network.comments)])))
        return "\n".join(details)

    def format_html(self, nlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/network/%(ip)s.html">%(ip)s</a></li>"""
            % {"ip": network.ip} for ip in shlist])

ObjectFormatter.handlers[SimpleNetworkList] = SimpleNetworkListFormatter()


#if __name__=='__main__':
