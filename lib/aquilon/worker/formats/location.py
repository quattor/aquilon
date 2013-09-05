# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Location formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Location, Rack, Building


class LocationFormatter(ObjectFormatter):
    def format_raw(self, location, indent=""):
        details = [indent + "{0:c}: {0.name}".format(location)]
        if location.fullname:
            details.append(indent + "  Fullname: %s" % location.fullname)
        if hasattr(location, 'timezone'):
            details.append(indent + "  Timezone: %s" % location.timezone)
        # Rack could have been a separate formatter, but since this is
        # the only difference...
        if isinstance(location, Rack):
            details.append(indent + "  Row: %s" % location.rack_row)
            details.append(indent + "  Column: %s" % location.rack_column)
        elif isinstance(location, Building):
            details.append(indent + "  Address: %s" % location.address)
        if location.comments:
            details.append(indent + "  Comments: %s" % location.comments)
        if location.parents:
            details.append(indent + "  Location Parents: [%s]" %
                           ", ".join(format(p) for p in location.parents))
        if location.default_dns_domain:
            details.append(indent + "  Default DNS Domain: %s" %
                           location.default_dns_domain)
        return "\n".join(details)

    def format_proto(self, loc, container):
        skeleton = container.locations.add()
        skeleton.name = str(loc.name)
        skeleton.location_type = str(loc.location_type)
        skeleton.fullname = str(loc.fullname)
        if isinstance(loc, Rack) and loc.rack_row and loc.rack_column:
            skeleton.row = loc.rack_row
            skeleton.col = loc.rack_column
        if hasattr(loc, "timezone"):
            skeleton.timezone = loc.timezone

        for p in loc.parents:
            parent = skeleton.parents.add()
            parent.name = p.name
            parent.location_type = p.location_type

    def csv_fields(self, location):
        details = [location.location_type, location.name]
        if location.parent:
            details.append(location.parent.location_type)
            details.append(location.parent.name)
        else:
            details.extend([None, None])

        if isinstance(location, Rack):
            details.append(location.rack_row)
            details.append(location.rack_column)
        else:
            details.extend([None, None])

        if hasattr(location, 'timezone'):
            details.append(location.timezone)
        else:
            details.extend([None])

        details.append(location.fullname)

        return details


class LocationList(list):
    """Holds a list of locations for which a location list will be formatted
    """
    pass


class LocationListFormatter(ListFormatter):
    pass

for location_type, mapper in Location.__mapper__.polymorphic_map.items():
    ObjectFormatter.handlers[mapper.class_] = LocationFormatter()

ObjectFormatter.handlers[LocationList] = LocationListFormatter()


class SimpleLocationList(list):
    """Holds a list of locations for which a location list will be formatted
       in a simple (name-only) manner."""
    pass


class SimpleLocationListFormatter(LocationListFormatter):
    template_html = "simple_location_list.mako"

    def format_raw(self, result, indent=""):
        return str("\n".join([indent + location.name for location in result]))

    def csv_fields(self, location):
        return (location.name,)


ObjectFormatter.handlers[SimpleLocationList] = SimpleLocationListFormatter()
