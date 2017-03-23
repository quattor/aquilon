# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2016  Contributor
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
""" Formatter for cluster AutoStartList and SystemList tables. """

from operator import attrgetter

from aquilon.aqdb.model import AutoStartList, SystemList, BundleResource
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter


class PriorityListFormatter(ResourceFormatter):

    resource_field = None
    priority_attribute = "priority"

    def fill_proto(self, pri_list, skeleton, embedded=True, indirect_attrs=True):
        super(PriorityListFormatter, self).fill_proto(pri_list, skeleton)
        holder = pri_list.holder
        dbcluster = holder.toplevel_holder_object
        if isinstance(holder, BundleResource):
            rg = holder.resourcegroup.name
        else:
            rg = None

        container_proxy = getattr(skeleton, self.resource_field)
        for entry in pri_list.entries.values():
            msg = container_proxy.add()
            msg.cluster = dbcluster.name
            if rg:
                msg.rg = rg
            msg.member = str(entry.host)
            setattr(msg, self.priority_attribute, entry.priority)


class SystemListFormatter(PriorityListFormatter):

    suppress_name = True
    resource_field = "systemlist"

    def extra_details(self, sl, indent=""):
        details = []
        for entry in sorted(sl.entries.values(), key=attrgetter("priority")):
            details.append(indent + "  Member: %s Priority: %d" %
                           (entry.host, entry.priority))
        return details

ObjectFormatter.handlers[SystemList] = SystemListFormatter()


class AutoStartListFormatter(PriorityListFormatter):

    suppress_name = True
    resource_field = "autostartlist"
    priority_attribute = "order_idx"

    def extra_details(self, asl, indent=""):
        details = []
        for entry in sorted(asl.entries.values(),
                            key=attrgetter("priority", "member.node_index")):
            details.append(indent + "  Member: %s Order: %d" %
                           (entry.host, entry.priority))
        return details

ObjectFormatter.handlers[AutoStartList] = AutoStartListFormatter()
