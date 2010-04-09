# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""DNS Domain formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import DnsDomain


class DnsDomainFormatter(ObjectFormatter):
    def format_raw(self, dns_domain, indent=""):
        details = [indent + "DNS Domain: %s" % dns_domain.name]
        if dns_domain.comments:
            details.append(indent + "  Comments: %s" % dns_domain.comments)
        return "\n".join(details)

    def csv_fields(self, dns_domain):
        return (dns_domain.name, dns_domain.comments)


class DNSDomainList(list):
    """By convention, holds DnsDomain objects."""
    pass


class DNSDomainListFormatter(ListFormatter):

    protocol = "aqddnsdomains_pb2"

    def format_proto(self, dns_domain_list, skeleton=None):
        dns_domain_list_msg = \
                self.loaded_protocols[self.protocol].DNSDomainList()
        for dns_domain in dns_domain_list:
            self.add_dns_domain_msg(dns_domain_list_msg.dns_domains.add(),
                                    dns_domain)
        return dns_domain_list_msg.SerializeToString()

    def csv_fields(self, dns_domain):
        return (dns_domain.name, dns_domain.comments)

ObjectFormatter.handlers[DnsDomain] = DnsDomainFormatter()
ObjectFormatter.handlers[DNSDomainList] = DNSDomainListFormatter()
