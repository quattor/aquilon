# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2017,2018  Contributor
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
"""Dynamic range formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter


class DynamicRange(object):
    def __init__(self, network, start, end, range_class):
        self.network = network
        self.start = start
        self.end = end
        self.range_class = range_class


class DynamicRangeFormatter(ObjectFormatter):

    def format_raw(self, range, indent="", embedded=True, indirect_attrs=True):
        details = [indent + "Dynamic Range: %s - %s" % (range.start, range.end)]
        details.append(indent + "  Size: %d" %
                       (int(range.end) - int(range.start) + 1))
        details.append(indent + "  Network: %s" % range.network)
        if range.range_class:
            details.append(indent + "  Range Class: %s" % range.range_class)
        return "\n".join(details)


ObjectFormatter.handlers[DynamicRange] = DynamicRangeFormatter()
