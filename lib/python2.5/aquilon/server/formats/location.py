# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Location formatter."""


from inspect import isclass

from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.loc.location import Location
from aquilon.aqdb.loc.company import Company
from aquilon.aqdb.loc.hub import Hub
from aquilon.aqdb.loc.continent import Continent
from aquilon.aqdb.loc.country import Country
from aquilon.aqdb.loc.campus import Campus
from aquilon.aqdb.loc.city import City
from aquilon.aqdb.loc.building import Building
from aquilon.aqdb.loc.rack import Rack
from aquilon.aqdb.loc.desk import Desk


class LocationFormatter(ObjectFormatter):
    def format_raw(self, location, indent=""):
        details = [indent + "%s: %s" %
                (location.location_type.capitalize(), location.name)]
        if location.fullname:
            details.append(indent + "  Fullname: %s" % location.fullname)
        # Rack could have been a separate formatter, but since this is
        # the only difference...
        if isinstance(location, Rack):
            details.append(indent + "  Row: %s" % location.rack_row)
            details.append(indent + "  Column: %s" % location.rack_column)
        if location.comments:
            details.append(indent + "  Comments: %s" % location.comments)
        if location.parents:
            details.append(indent + "  Location Parents: [%s]" %
                    ", ".join("%s: %s" % (p.location_type.capitalize(), p.name)
                    for p in location.parents))
        return "\n".join(details)

    def format_csv(self, location):
        # We have no policy around quoting CSV yet... leaving off fullname
        # for now.
        details = [location.location_type, location.name]
        if location.parent:
            details.append(location.parent.location_type)
            details.append(location.parent.name)
        else:
            details.append("")
            details.append("")
        if isinstance(location, Rack):
            details.append(location.rack_row)
            details.append(location.rack_column)
        cleaned = []
        for d in details:
            if d is None:
                cleaned.append("")
            else:
                cleaned.append(str(d))
        return ",".join(cleaned)


# Laziness... grab any imported Location classes and handle them above.
for location_type in globals().values():
    if not isclass(location_type):
        continue
    if issubclass(location_type, Location):
        ObjectFormatter.handlers[location_type] = LocationFormatter()


