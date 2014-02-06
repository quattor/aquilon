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
"""List formatter."""

from operator import attrgetter

from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.query import Query

from aquilon.worker.formats.formatters import ObjectFormatter


class ListFormatter(ObjectFormatter):
    def format_raw(self, result, indent=""):
        if hasattr(self, "template_raw"):
            return ObjectFormatter.format_raw(self, result, indent)
        return "\n".join([self.redirect_raw(item, indent) for item in result])

    def format_csv(self, result, writer):
        for item in result:
            self.redirect_csv(item, writer)

    def format_html(self, result):
        if hasattr(self, "template_html"):
            return ObjectFormatter.format_html(self, result)
        return "<ul>\n<li>" + "<li>\n<li>".join(
                [self.redirect_html(item) for item in result]
                ) + "</li>\n</ul>\n"

    def format_djb(self, result):
        return "\n".join([self.redirect_djb(item) for item in result])

    def format_proto(self, result, container):
        for item in result:
            self.redirect_proto(item, container)

ObjectFormatter.handlers[list] = ListFormatter()
ObjectFormatter.handlers[Query] = ListFormatter()
ObjectFormatter.handlers[InstrumentedList] = ListFormatter()


class StringList(list):
    pass


class StringListFormatter(ListFormatter):
    """ Format a list of object as strings, regardless of type """

    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(obj) for obj in objects])

    def format_csv(self, objects, writer):
        for obj in objects:
            writer.writerow((str(obj),))

ObjectFormatter.handlers[StringList] = StringListFormatter()


class StringAttributeList(list):
    def __init__(self, items, attr):
        if isinstance(attr, basestring):
            self.getter = attrgetter(attr)
        else:
            self.getter = attr
        super(StringAttributeList, self).__init__(items)


class StringAttributeListFormatter(ListFormatter):
    """ Format a single attribute of every object as a string """

    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(objects.getter(obj)) for obj in objects])

    def format_csv(self, objects, writer):
        for obj in objects:
            writer.writerow((str(objects.getter(obj)),))

ObjectFormatter.handlers[StringAttributeList] = StringAttributeListFormatter()
