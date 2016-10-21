# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
""" Operating System formatter """

from operator import attrgetter

from aquilon.aqdb.model import OperatingSystem
from aquilon.worker.formats.formatters import ObjectFormatter


class OSFormatter(ObjectFormatter):
    def format_raw(self, os, indent="", embedded=True, indirect_attrs=True):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(os))
        details.append(indent + "  Version: %s" % os.version)
        if not embedded:
            details.append(indent + "  Archetype: %s" % os.archetype)
        for dbsrv in sorted(os.required_services, key=attrgetter("name")):
            details.append(indent + "  Required Service: %s" % dbsrv.name)
        details.append(indent + "  Lifecycle: %s" % os.lifecycle)
        if os.comments:
            details.append(indent + "  Comments: %s" % os.comments)

        return "\n".join(details)

    def fill_proto(self, os, skeleton, embedded=True, indirect_attrs=True):
        skeleton.name = os.name
        skeleton.version = os.version

        lifecycle_enum = skeleton.DESCRIPTOR.fields_by_name['lifecycle'].enum_type
        skeleton.lifecycle = lifecycle_enum.values_by_name[os.lifecycle.name.upper()].number

        # We don't need the services here, so don't call redirect_proto()
        self.redirect_proto(os.archetype, skeleton.archetype,
                            indirect_attrs=False)

ObjectFormatter.handlers[OperatingSystem] = OSFormatter()
