# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Host formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.sy.host import Host


class HostFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"
    def format_raw(self, host, indent=""):
        details = [ indent + "Hostname: %s" % host.fqdn ]
        if host.ip:
            details.append(indent + "  IP: %s" % host.ip)
        details.append(self.redirect_raw(host.machine, indent+"  "))
        details.append(self.redirect_raw(host.archetype, indent+"  "))
        details.append(self.redirect_raw(host.domain, indent+"  "))
        details.append(self.redirect_raw(host.status, indent+"  "))
        for build_item in host.templates:
            details.append(self.redirect_raw(build_item.cfg_path, indent+"  "))
        if host.comments:
            details.append(indent + "  Comments: %s" % host.comments)
        return "\n".join(details)

    def format_proto(self, host):
        # we actually want to return a SimpleHostList of one host...
        shlf = SimpleHostListFormatter()
        return(shlf.format_proto([host]))

ObjectFormatter.handlers[Host] = HostFormatter()


class SimpleHostList(list):
    """By convention, holds a list of hosts to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleHostListFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"
    
    def format_raw(self, shlist, indent=""):
        return str("\n".join([indent + host.fqdn for host in shlist]))

    # Should probably display some useful info...
    def format_csv(self, shlist):
        return str("\n".join([host.fqdn for host in shlist]))

    def format_html(self, shlist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/host/%(fqdn)s.html">%(fqdn)s</a></li>"""
            % {"fqdn": host.fqdn} for host in shlist])

    def format_proto(self, shlist):
        hostlist_msg = self.loaded_protocols[self.protocol].HostList()
        for h in shlist:
            self.add_host_msg(hostlist_msg.hosts.add(), h)
        return hostlist_msg.SerializeToString()

ObjectFormatter.handlers[SimpleHostList] = SimpleHostListFormatter()


class HostIPList(list):
    """ By convention, holds tuples of host_name, interface_ip, primary.
        The third field is only used for auxiliary systems, and
        supplies the primary host name.  This allows reverse lookups
        to resolve back to the primary name."""
    pass


class HostIPListFormatter(ObjectFormatter):
    def format_csv(self, hilist):
        return str("\n".join([",".join(entry) for entry in hilist]))

ObjectFormatter.handlers[HostIPList] = HostIPListFormatter()


class HostMachineList(list):
    """By convention, holds Host objects."""
    pass


class HostMachineListFormatter(ObjectFormatter):
    def format_csv(self, hlist):
        return str("\n".join([str.join(",",(host.fqdn, host.machine.name)) for host in hlist]))

ObjectFormatter.handlers[HostMachineList] = HostMachineListFormatter()


