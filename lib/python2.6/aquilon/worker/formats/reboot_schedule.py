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
"""RebootSchedule Resource formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import RebootSchedule


class RebootScheduleFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def extra_details(self, rs, indent=""):
        details = []
        details.append(indent + "  Week: {0.week}".format(rs))
        details.append(indent + "  Day: {0.day}".format(rs))
        details.append(indent + "  Time: {0.time}".format(rs))
        return details

    def format_proto(self, rs, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        # XXX: The protocol resource spec does not have these values.
        #skeleton.rsdata.week = str(rs.week)
        #skeleton.rsdata.day = str(rs.day)
        #skeleton.rsdata.time = str(rs.time)
        return super(RebootScheduleFormatter, self).format_proto(rs, skeleton)


ObjectFormatter.handlers[RebootSchedule] = RebootScheduleFormatter()
