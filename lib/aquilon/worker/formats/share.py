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
"""Share Resource formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import Share


class ShareFormatter(ResourceFormatter):

    def extra_details(self, share, indent=""):
        details = []

        if share.latency_threshold:
            details.append(indent + "  Latency threshold: %d" %
                           share.latency_threshold)

        details.append(indent + "  Server: %s" % share.server)
        details.append(indent + "  Mountpoint: %s" % share.mount)
        details.append(indent + "  Disk Count: %d" % share.disk_count)
        details.append(indent + "  Machine Count: %d" % share.machine_count)

        return details

    def format_proto(self, share, container):
        skeleton = container.resources.add()
        self.add_resource_data(skeleton, share)
        if share.server:
            skeleton.share.server = share.server
        if share.mount:
            skeleton.share.mount = share.mount
        skeleton.share.disk_count = share.disk_count
        skeleton.share.machine_count = share.machine_count

ObjectFormatter.handlers[Share] = ShareFormatter()
