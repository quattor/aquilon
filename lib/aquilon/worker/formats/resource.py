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
"""Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Resource


class ResourceFormatter(ObjectFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, share, indent=""):
        return []

    def format_raw(self, resource, indent=""):
        details = []
        details.append(indent + "{0:c}: {0.name}".format(resource))
        if resource.comments:
            details.append(indent + "  Comments: %s" % resource.comments)

        details.append(indent + "  Bound to: {0}"
                       .format(resource.holder.holder_object))
        details.extend(self.extra_details(resource, indent))
        return "\n".join(details)

    def format_proto(self, resource, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        skeleton.name = str(resource.name)
        skeleton.type = str(resource.resource_type)
        return container


ObjectFormatter.handlers[Resource] = ResourceFormatter()


class ResourceList(list):
    pass


class ResourceListFormatter(ListFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, reslist, indent=""):
        details = []
        for resource in reslist:
            details.append(self.redirect_raw(resource, indent))
        return "\n".join(details)

    def format_proto(self, reslist, skeleton=None):
        if not skeleton:
            skeleton = self.loaded_protocols[self.protocol].ResourceList()
        for resource in reslist:
            self.redirect_proto(resource, skeleton.resources.add())
        return skeleton


ObjectFormatter.handlers[ResourceList] = ResourceListFormatter()
