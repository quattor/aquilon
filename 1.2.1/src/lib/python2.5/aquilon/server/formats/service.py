#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Service formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.svc.service import Service


class ServiceFormatter(ObjectFormatter):
    def format_raw(self, service, indent=""):
        details = [indent + "Service: %s" % service.name]
        details.append(self.redirect_raw(service.cfg_path, indent+"  "))
        if service.comments:
            details.append(indent + "  Comments: %s" % service.comments)
        for instance in service.instances:
            details.append(self.redirect_raw(instance, indent+"  "))
        return "\n".join(details)

ObjectFormatter.handlers[Service] = ServiceFormatter()


#if __name__=='__main__':
