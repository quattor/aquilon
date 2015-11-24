# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""ServiceMap formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import ServiceMap


class ServiceMapFormatter(ObjectFormatter):
    def format_raw(self, sm, indent="", embedded=True, indirect_attrs=True):
        details = []
        if sm.personality:
            details.append("{0:c}: {0.name} {1:c}: {1.name}"
                           .format(sm.personality.archetype, sm.personality))
        else:
            details.append("Archetype: aquilon")

        details.append("{0:c}: {0.name} Instance: {1.name}"
                       .format(sm.service_instance.service,
                               sm.service_instance))
        details.append("Map: {0}".format(sm.mapped_to))

        return indent + " ".join(details)

    def fill_proto(self, service_map, skeleton, embedded=True,
                   indirect_attrs=True):
        if service_map.location:
            self.redirect_proto(service_map.location, skeleton.location,
                                indirect_attrs=False)
        else:
            self.redirect_proto(service_map.network, skeleton.network,
                                indirect_attrs=False)

        self.redirect_proto(service_map.service_instance, skeleton.service,
                            indirect_attrs=False)

        if service_map.personality:
            self.redirect_proto(service_map.personality, skeleton.personality,
                                indirect_attrs=False)
        else:
            skeleton.personality.archetype.name = 'aquilon'

ObjectFormatter.handlers[ServiceMap] = ServiceMapFormatter()
