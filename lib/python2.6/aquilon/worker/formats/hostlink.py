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
"""Hostlink Resource formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Hostlink


class HostlinkFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, hostlink, indent=""):
        details = []
        details.append(indent + "  Target Path: %s" % hostlink.target)
        details.append(indent + "  Owner: %s" % hostlink.owner_user)
        if hostlink.owner_group is not None:
            details.append(indent + "  Group: %s" % hostlink.owner_group)
        return details

    def format_proto(self, hostlink, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        skeleton.hostlink.target = hostlink.target
        skeleton.hostlink.owner_user = hostlink.owner_user
        if hostlink.owner_group:
            skeleton.hostlink.owner_group = hostlink.owner_group
        return super(HostlinkFormatter, self).format_proto(hostlink,
                                                           skeleton)


ObjectFormatter.handlers[Hostlink] = HostlinkFormatter()
