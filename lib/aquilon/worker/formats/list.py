# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
from sqlalchemy.ext.associationproxy import _AssociationList

from aquilon.worker.formats.formatters import ObjectFormatter


class ListFormatter(ObjectFormatter):
    def format_raw(self, result, indent="", embedded=True,
                   indirect_attrs=True):
        if hasattr(self, "template_raw"):
            return ObjectFormatter.format_raw(self, result, indent,
                                              embedded=embedded,
                                              indirect_attrs=indirect_attrs)
        return "\n".join(self.redirect_raw(item, indent, embedded=embedded,
                                           indirect_attrs=indirect_attrs)
                         for item in result)

    def format_csv(self, result, writer):
        for item in result:
            self.redirect_csv(item, writer)

    def format_html(self, result):
        if hasattr(self, "template_html"):
            return ObjectFormatter.format_html(self, result)
        return "<ul>\n<li>" + "<li>\n<li>".join(
            self.redirect_html(item) for item in result) + "</li>\n</ul>\n"

    def format_djb(self, result):
        return "\n".join(self.redirect_djb(item) for item in result)

    def format_proto(self, result, container, embedded=True, indirect_attrs=True):
        for item in result:
            skeleton = container.add()
            ObjectFormatter.redirect_proto(item, skeleton, embedded=embedded,
                                           indirect_attrs=indirect_attrs)

ObjectFormatter.handlers[list] = ListFormatter()
ObjectFormatter.handlers[Query] = ListFormatter()
ObjectFormatter.handlers[InstrumentedList] = ListFormatter()
ObjectFormatter.handlers[_AssociationList] = ListFormatter()


class StringList(list):
    pass


class StringListFormatter(ListFormatter):
    """ Format a list of object as strings, regardless of type """

    def format_raw(self, objects, indent="", embedded=True, indirect_attrs=True):
        return "\n".join(indent + str(obj) for obj in objects)

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

    def format_raw(self, objects, indent="", embedded=True, indirect_attrs=True):
        return "\n".join(indent + str(objects.getter(obj)) for obj in objects)

    def format_csv(self, objects, writer):
        for obj in objects:
            writer.writerow((str(objects.getter(obj)),))

    def format_proto(self, objects, container, embedded=True, indirect_attrs=True):
        # This method always populates the first field of the protobuf message,
        # regardless of how that field is called.

        field_name = None
        for obj in objects:
            msg = container.add()
            if not field_name:
                field_name = msg.DESCRIPTOR.fields[0].name
            setattr(msg, field_name, str(objects.getter(obj)))
            # TODO: if obj is really the full DB object rather than just a
            # string, and it has other attributes already loaded, then we could
            # add those attributes to the protobuf message "for free". Let's see
            # if a usecase comes up.

ObjectFormatter.handlers[StringAttributeList] = StringAttributeListFormatter()
