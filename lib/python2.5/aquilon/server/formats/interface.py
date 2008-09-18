#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Interface formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.interface import Interface


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        #details = [indent + "Interface: %s" % interface.name,
        #           indent + "  MAC: %s" % interface.mac,
        #           indent + "  IP: %s" % interface.ip,
        #           indent + "  Bootable: %s" % interface.bootable]
        #return "\n".join(details)
        return indent + "Interface: %s %s boot=%s" % (interface.name,
                interface.mac, interface.bootable)

ObjectFormatter.handlers[Interface] = InterfaceFormatter()


class MissingManagersList(list):
    pass

class MissingManagersFormatter(ObjectFormatter):
    def format_raw(self, mmlist, indent=""):
        commands = []
        for interface in mmlist:
            host = interface.hardware_entity.host
            if host:
                # FIXME: Deal with multiple management interfaces?
                commands.append("aq add manager --hostname '%s' --ip 'IP'" %
                                host.fqdn)
            else:
                commands.append("# No host found for machine %s with management interface" %
                                interface.hardware_entity.name)
        return "\n".join(commands)

    def format_csv(self, mmlist):
        hosts = []
        for interface in mmlist:
            host = interface.hardware_entity.host
            if host:
                # FIXME: Deal with multiple management interfaces?
                hosts.append(host.fqdn)
        return "\n".join(hosts)

ObjectFormatter.handlers[MissingManagersList] = MissingManagersFormatter()


#if __name__=='__main__':
