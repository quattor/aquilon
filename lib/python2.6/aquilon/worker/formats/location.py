# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Location formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Location, Rack, Building


class LocationFormatter(ObjectFormatter):
    protocol = "aqdlocations_pb2"

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

    def format_proto(self, loc, skeleton=None):
        loclistf = LocationListFormatter()
        return(loclistf.format_proto([loc], skeleton))

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
    protocol = "aqdlocations_pb2"

    def format_proto(self, result, skeleton=None):
        loclist_msg = self.loaded_protocols[self.protocol].LocationList()
        for loc in result:
            msg = loclist_msg.locations.add()
            msg.name = str(loc.name)
            msg.location_type = str(loc.location_type)
            msg.fullname = str(loc.fullname)
            if isinstance(loc, Rack) and loc.rack_row and loc.rack_column:
                msg.row = loc.rack_row
                msg.col = loc.rack_column
            if hasattr(loc, "timezone"):
                msg.timezone = loc.timezone

            for p in loc.parents:
                parent = msg.parents.add()
                parent.name = p.name
                parent.location_type = p.location_type

        return loclist_msg.SerializeToString()


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
