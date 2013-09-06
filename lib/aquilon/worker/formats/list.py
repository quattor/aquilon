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

import csv
import cStringIO
from operator import attrgetter

from sqlalchemy.orm.collections import InstrumentedList
from sqlalchemy.orm.query import Query

from aquilon.worker.formats.formatters import ObjectFormatter


class ListFormatter(ObjectFormatter):
    def format_raw(self, result, indent=""):
        if hasattr(self, "template_raw"):
            return ObjectFormatter.format_raw(self, result, indent)
        return "\n".join([self.redirect_raw(item, indent) for item in result])

    def csv_fields(self, result):
        # Delegate the field selection according to the result's class, but
        # avoid calling ourselves recursively.
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        if handler.__class__ == self.__class__:
            return super(ListFormatter, self).csv_fields(result)
        return handler.csv_fields(result)

    def csv_tolist(self, result):
        # Delegate the conversion according to the result's class, but
        # avoid calling ourselves recursively.
        handler = ObjectFormatter.handlers.get(result.__class__,
                                               ObjectFormatter.default_handler)
        if handler.__class__ == self.__class__:
            return super(ListFormatter, self).csv_tolist(result)
        return handler.csv_tolist(result)

    def format_csv(self, result):
        # This is an optimization to use a single buffer/writer for all elements
        # of the list instead of creating one for every element
        strbuf = cStringIO.StringIO()
        writer = csv.writer(strbuf, dialect='aquilon')
        for obj in result:
            for item in self.csv_tolist(obj):
                fields = self.csv_fields(item)
                if fields:
                    writer.writerow(fields)
        return strbuf.getvalue()

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

ObjectFormatter.handlers[StringAttributeList] = StringAttributeListFormatter()
