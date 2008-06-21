#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Location formatter."""


from inspect import isclass

from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.location import (Location, Company, Hub,
        Continent, Country, City, Building, Rack, Chassis, Desk)


class LocationFormatter(ObjectFormatter):
    def format_raw(self, location, indent=""):
        details = [indent + "%s: %s" %
                (location.type.type.capitalize(), location.name)]
        if location.fullname:
            details.append(indent + "  Fullname: %s" % location.fullname)
        if location.comments:
            details.append(indent + "  Comments: %s" % location.comments)
        if location.parents:
            details.append(indent + "  Location Parents: [%s]" %
                    ", ".join("%s: %s" % (p.type.type.capitalize(), p.name)
                    for p in location.parents))
        return "\n".join(details)

# Laziness... grab any imported Location classes and handle them above.
for location_type in globals().values():
    if not isclass(location_type):
        continue
    if issubclass(location_type, Location):
        ObjectFormatter.handlers[location_type] = LocationFormatter()


#if __name__=='__main__':
