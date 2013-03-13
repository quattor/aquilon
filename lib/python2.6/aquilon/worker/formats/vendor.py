# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2013  Contributor
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


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Vendor


class VendorFormatter(ObjectFormatter):
    def format_raw(self, vendor, indent=""):
        details = [indent + "Vendor: %s" % vendor.name]
        if vendor.comments:
            details.append(indent + "  Comments: %s" % vendor.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Vendor] = VendorFormatter()
