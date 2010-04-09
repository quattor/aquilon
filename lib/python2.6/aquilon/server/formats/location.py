# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from inspect import isclass

from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (Location, Company, Hub, Continent, Country,
                                Campus, City, Building, Room, Rack, Desk)


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

    def csv_fields(self, location):
        # TODO: We have no policy around quoting CSV yet... leaving off fullname
        # for now.
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
        return details


# Laziness... grab any imported Location classes and handle them above.
for location_type in globals().values():
    if not isclass(location_type):
        continue
    if issubclass(location_type, Location):
        ObjectFormatter.handlers[location_type] = LocationFormatter()
