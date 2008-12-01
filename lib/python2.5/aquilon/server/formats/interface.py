# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Interface formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.hw.interface import Interface


class InterfaceFormatter(ObjectFormatter):
    def format_raw(self, interface, indent=""):
        details = [indent + "Interface: %s %s boot=%s" % (interface.name,
                                                          interface.mac,
                                                          interface.bootable),
                   indent + "  Type: %s" % interface.interface_type]
        hw = interface.hardware_entity
        hw_type = hw.hardware_entity_type
        if hw_type == 'machine':
            details.append(indent + "  Attached to: machine %s" % hw.name)
        elif hw_type == 'tor_switch_hw':
            if hw.tor_switch:
                details.append(indent + "  Attached to: tor_switch %s" %
                                   ",".join([ts.fqdn for ts in hw.tor_switch]))
            else:
                details.append("  Attached to: unnamed tor_switch")
        elif hw_type == 'chassis_hw':
            if hw.chassis_hw:
                details.append("  Attached to: chassis %s" %
                                   ",".join([c.fqdn for c in hw.chassis_hw]))
            else:
                details.append("  Attached to: unnamed chassis")
        elif getattr(hw, "name", None):
            details.append("  Attached to: %s" % hw.name)
        if interface.system:
            details.append(indent + "  Provides: %s [%s]" %
                           (interface.system.fqdn, interface.system.ip))
        return "\n".join(details)

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


