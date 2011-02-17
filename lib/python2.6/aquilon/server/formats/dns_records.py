# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
""" Formatting for all sorts of DNS Records """

#import aquilon.server.depends
from aquilon.aqdb.model import NsRecord
from aquilon.server.formats.list import ListFormatter
from aquilon.server.formats.formatters import ObjectFormatter


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
