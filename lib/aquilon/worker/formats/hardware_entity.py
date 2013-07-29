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


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import HardwareEntity


# Should never get invoked...
class HardwareEntityFormatter(ObjectFormatter):
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

ObjectFormatter.handlers[HardwareEntity] = HardwareEntityFormatter()


class SimpleHardwareEntityList(list):
    """By convention, holds a list of systems to be formatted in a simple
       (name-only) manner."""
    pass


class SimpleHardwareEntityListFormatter(ListFormatter):
    def format_raw(self, shelist, indent=""):
        return str("\n".join([indent + hw.label for hw in shelist]))

    # TODO: Should probably display some useful info...
    def csv_fields(self, hw):
        return (hw.label,)

    # Maybe delegate to each type...?  There is no simple/standard
    # name based hardware search.
    def format_html(self, shelist):
        return self.format_raw(shelist)

ObjectFormatter.handlers[SimpleHardwareEntityList] = \
        SimpleHardwareEntityListFormatter()
