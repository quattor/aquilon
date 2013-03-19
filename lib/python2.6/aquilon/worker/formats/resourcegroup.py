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
"""ResourceGroup Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import ResourceGroup


class ResourceGroupFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, rg, indent=""):
        details = []
        if rg.required_type:
            details.append(indent + "  Type: %s" % rg.required_type)

        if rg.resholder:
            for resource in rg.resholder.resources:
                details.append(self.redirect_raw(resource, indent + "  "))

        return details

    def format_proto(self, rg, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        if rg.required_type:
            skeleton.resourcegroup.required_type = rg.required_type
        if rg.resholder and rg.resholder.resources:
            for resource in rg.resholder.resources:
                r = skeleton.resourcegroup.resources.add()
                self.redirect_proto(resource, r)
        return super(ResourceGroupFormatter, self).format_proto(rg, skeleton)


ObjectFormatter.handlers[ResourceGroup] = ResourceGroupFormatter()
