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
from aquilon.aqdb.data_sync.storage import find_storage_data


class ShareFormatter(ResourceFormatter):

    def extra_details(self, share, indent=""):
        details = []

        share_info = find_storage_data(share)
        details.append(indent + "  Server: %s" % share_info["server"])
        details.append(indent + "  Mountpoint: %s" % share_info["mount"])
        details.append(indent + "  Disk Count: %d" % share.disk_count)
        details.append(indent + "  Machine Count: %d" % share.machine_count)

        return details

    def format_proto(self, share, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        share_info = find_storage_data(share)
        skeleton.share.server = share_info["server"]
        skeleton.share.mount = share_info["mount"]
        skeleton.share.disk_count = share.disk_count
        skeleton.share.machine_count = share.machine_count
        return super(ShareFormatter, self).format_proto(share, skeleton)


ObjectFormatter.handlers[Share] = ShareFormatter()
