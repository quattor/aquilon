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
"""DnsRecord formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import DnsRecord, DynamicStub, ARecord, ReservedName


class DnsRecordFormatter(ObjectFormatter):
    def format_raw(self, dns_record, indent=""):
        if dns_record.hardware_entity:
            return self.redirect_raw(dns_record.hardware_entity, indent)

        details = [indent + "{0:c}: {1!s}".format(dns_record, dns_record.fqdn)]
        details.append(indent + "  {0:c}: {0.name}".format(dns_record.fqdn.dns_environment))
        if dns_record.comments:
            details.append(indent + "  Comments: %s" % dns_record.comments)
        return "\n".join(details)

class ARecordFormatter(ObjectFormatter):
    def format_raw(self, dns_record, indent=""):
        if dns_record.hardware_entity:
            return self.redirect_raw(dns_record.hardware_entity, indent)

        details = [indent + "{0:c}: {1!s}".format(dns_record, dns_record.fqdn)]
        details.append(indent + "  {0:c}: {0.name}".format(dns_record.fqdn.dns_environment))
        details.append(indent + "  IP: %s" % dns_record.ip)
        details.append(indent + "  Network: %s" % dns_record.network.network)
        #details.append(indent + "    Network Environment: %s" %
        #               dns_record.network.network_environment)
        if dns_record.comments:
            details.append(indent + "  Comments: %s" % dns_record.comments)
        return "\n".join(details)

# The DnsRecord entry should never get invoked, we always have a subclass.
ObjectFormatter.handlers[DnsRecord] = DnsRecordFormatter()
ObjectFormatter.handlers[ReservedName] = DnsRecordFormatter()

ObjectFormatter.handlers[DynamicStub] = ARecordFormatter()
ObjectFormatter.handlers[ARecord] = ARecordFormatter()
