# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""HardwareEntity formatter."""

from operator import attrgetter

from aquilon.aqdb.model import HardwareEntity
from aquilon.worker.formats.formatters import ObjectFormatter


class HardwareEntityFormatter(ObjectFormatter):
    # Should never get invoked...
    def format_raw(self, hwe, indent=""):
        details = [indent + "%s: %s" % (hwe.hardware_type, hwe.label)]
        details.append(self.redirect_raw(hwe.location, indent + "  "))
        details.append(self.redirect_raw(hwe.model, indent + "  "))
        if hwe.serial_no:
            details.append(indent + "  Serial: %s" % hwe.serial_no)
        for i in hwe.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if hwe.comments:
            details.append(indent + "  Comments: %s" % hwe.comments)
        return "\n".join(details)

    @staticmethod
    def redirect_raw_host_details(result, indent=""):
        # A given hardware entity formatter may call this method, if/when it
        # has an associated host object, to include the details of the host.
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        return handler.format_raw_host_details(result, indent)


ObjectFormatter.handlers[HardwareEntity] = HardwareEntityFormatter()
