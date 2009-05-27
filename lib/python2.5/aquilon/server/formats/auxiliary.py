# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Auxiliary formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Auxiliary


class AuxiliaryFormatter(ObjectFormatter):
    def format_raw(self, auxiliary, indent=""):
        details = [ indent + "Auxiliary: %s" % auxiliary.fqdn ]
        if auxiliary.ip:
            details.append(indent + "  IP: %s" % auxiliary.ip)
        if auxiliary.mac:
            details.append(indent + "  MAC: %s" % auxiliary.mac)
        for i in auxiliary.interfaces:
            if i.system == auxiliary:
                details.append(self.redirect_raw(i, indent+"  "))
        details.append(self.redirect_raw(auxiliary.machine, indent+"  "))
        if auxiliary.comments:
            details.append(indent + "  Comments: %s" % auxiliary.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Auxiliary] = AuxiliaryFormatter()


