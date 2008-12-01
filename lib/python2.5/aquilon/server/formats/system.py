# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""System formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.sy.system import System
# Pull this in, at least temporarily, because *nothing* else references it
from aquilon.aqdb.sy.console_server import ConsoleServer


# Should never get invoked...
class SystemFormatter(ObjectFormatter):
    def format_raw(self, system, indent=""):
        details = [ indent + "%s: %s" % (system.system_type, system.fqdn) ]
        if system.ip:
            details.append(indent + "  IP: %s" % system.ip)
        if system.mac:
            details.append(indent + "  MAC: %s" % system.mac)
        if system.comments:
            details.append(indent + "  Comments: %s" % system.comments)
        return "\n".join(details)

ObjectFormatter.handlers[System] = SystemFormatter()


class SimpleSystemList(list):
    """By convention, holds a list of systems to be formatted in a simple
       (fqdn-only) manner."""
    pass


class SimpleSystemListFormatter(ObjectFormatter):
    def format_raw(self, sslist, indent=""):
        return str("\n".join([indent + system.fqdn for system in sslist]))

    # Should probably display some useful info...
    def format_csv(self, sslist):
        return str("\n".join([system.fqdn for system in sslist]))

    def format_html(self, sslist):
        return "<ul>\n%s\n</ul>\n" % "\n".join([
            """<li><a href="/system/%(fqdn)s.html">%(fqdn)s</a></li>"""
            % {"fqdn": system.fqdn} for system in sslist])

ObjectFormatter.handlers[SimpleSystemList] = SimpleSystemListFormatter()


