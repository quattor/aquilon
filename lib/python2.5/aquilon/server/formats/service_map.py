#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""ServiceMap formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.svc.service_map import ServiceMap


class ServiceMapFormatter(ObjectFormatter):
    def format_raw(self, sm, indent=""):
        return indent + "Service: %s Instance: %s Map: %s %s" % (
                sm.service.name, sm.service_instance.name,
                sm.location.location_type.capitalize(), sm.location.name)

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()


#if __name__=='__main__':
