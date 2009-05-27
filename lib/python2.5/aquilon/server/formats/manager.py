# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Manager formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Manager


class ManagerFormatter(ObjectFormatter):
    def format_raw(self, manager, indent=""):
        details = [ indent + "Manager: %s" % manager.fqdn ]
        if manager.ip:
            details.append(indent + "  IP: %s" % manager.ip)
        if manager.mac:
            details.append(indent + "  MAC: %s" % manager.mac)
        for i in manager.interfaces:
            if i.system == manager:
                details.append(self.redirect_raw(i, indent+"  "))
        details.append(self.redirect_raw(manager.machine, indent+"  "))
        if manager.comments:
            details.append(indent + "  Comments: %s" % manager.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Manager] = ManagerFormatter()


