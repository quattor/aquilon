# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""List formatter."""


import csv
import cStringIO

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

    def format_proto(self, result, skeleton=None):
        for item in result:
            skeleton = self.redirect_proto(item, skeleton)
        return skeleton

ObjectFormatter.handlers[list] = ListFormatter()
ObjectFormatter.handlers[Query] = ListFormatter()
ObjectFormatter.handlers[InstrumentedList] = ListFormatter()


class StringList(list):
    pass


class StringListFormatter(ListFormatter):
    """ Format a list of object as strings, regardless of type """

    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(obj) for obj in objects])

    def format_csv(self, objects):
        # Optimized version to skip the csv_tolist() redirections
        strbuf = cStringIO.StringIO()
        writer = csv.writer(strbuf, dialect='aquilon')
        for obj in objects:
            writer.writerow((str(obj),))
        return strbuf.getvalue()


ObjectFormatter.handlers[StringList] = StringListFormatter()


class StringAttributeList(list):
    def __init__(self, items, attr_name):
        self.attr_name = attr_name
        super(StringAttributeList, self).__init__(items)


class StringAttributeListFormatter(ListFormatter):
    """ Format a single attribute of every object as a string """

    def format_raw(self, objects, indent=""):
        return "\n".join([indent + str(getattr(obj, objects.attr_name))
                          for obj in objects])

    def format_csv(self, objects):
        # Optimized version to skip the csv_tolist() redirections
        strbuf = cStringIO.StringIO()
        writer = csv.writer(strbuf, dialect='aquilon')
        for obj in objects:
            writer.writerow((str(getattr(obj, objects.attr_name)),))
        return strbuf.getvalue()


ObjectFormatter.handlers[StringAttributeList] = StringAttributeListFormatter()
