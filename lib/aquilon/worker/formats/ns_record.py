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
""" Formatting for all sorts of DNS Records """

#import aquilon.worker.depends
from aquilon.aqdb.model import NsRecord
from aquilon.worker.formats.list import ListFormatter
from aquilon.worker.formats.formatters import ObjectFormatter


class NsRecordFormatter(ObjectFormatter):
    template_raw = "ns_record.mako"

    def csv_fields(self, ns):
        return (ns.dns_domain.name, ns.a_record.fqdn)

    def format_djb(self, ns):
        return ".%s::%s" % (ns.dns_domain.name, ns.a_record.fqdn)

ObjectFormatter.handlers[NsRecord] = NsRecordFormatter()


class SimpleNSRecordList(list):
    """By convention, holds a list of ns_records to be formatted in a simple
       (dns_domain: fqdn-only) manner."""
    pass


class SimpleNSRecordListFormatter(ListFormatter):
    def format_raw(self, snsrlist, indent=""):
        #return [self.redirect_raw(ns) for ns in snsrlist]
        #return str("\n".join(
        #    [indent + ns.dns_domain.name + ": " + ns.a_record.fqdn for ns in snsrlist]))

        return str("\n".join(
            [indent + self.redirect_raw(ns) for ns in snsrlist]))


ObjectFormatter.handlers[SimpleNSRecordList] = SimpleNSRecordListFormatter()
