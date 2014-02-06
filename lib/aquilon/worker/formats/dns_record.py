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
"""DnsRecord formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (DnsRecord, DynamicStub, ARecord, Alias,
                                ReservedName, SrvRecord)


class DnsRecordFormatter(ObjectFormatter):
    template_raw = "dns_record.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name, None)


class ARecordFormatter(ObjectFormatter):
    template_raw = "a_record.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               'A', dns_record.ip)


class AliasFormatter(ObjectFormatter):
    template_raw = "alias.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               'CNAME', dns_record.target)


class SrvRecordFormatter(ObjectFormatter):
    template_raw = "srv_record.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               'SRV', dns_record.priority, dns_record.weight,
                dns_record.target, dns_record.port)

# The DnsRecord entry should never get invoked, we always have a subclass.
ObjectFormatter.handlers[DnsRecord] = DnsRecordFormatter()
ObjectFormatter.handlers[ReservedName] = DnsRecordFormatter()

ObjectFormatter.handlers[DynamicStub] = ARecordFormatter()
ObjectFormatter.handlers[ARecord] = ARecordFormatter()

ObjectFormatter.handlers[Alias] = AliasFormatter()

ObjectFormatter.handlers[SrvRecord] = SrvRecordFormatter()


def inaddr_ptr(ip):
    octets = str(ip).split('.')
    octets.reverse()
    return "%s.in-addr.arpa" % '.'.join(octets)


def octal16(value):
    return "\\%03o\\%03o" % (value >> 8, value & 0xff)


def str8(text):
    return "\\%03o" % len(text) + text.replace(':', '\\072')


def nstr(text):
    return "".join(str8(p) for p in (text + ".").split('.'))


class DnsDump(list):
    def __init__(self, records, dns_domains):
        # Store a reference to the DNS domains to prevent them being evicted
        # from the session's cache
        self.dns_domains = dns_domains
        super(DnsDump, self).__init__(records)


class DnsDumpFormatter(ObjectFormatter):
    # Class for producing full DNS dumps. The type of a record alone is not
    # always enough to decide how to dump it, so we don't use the individual
    # record formatters.

    def format_raw(self, dump, indent=""):
        result = []
        # The output is not the most readable as we don't make use of $ORIGIN,
        # but BIND should be able to digest it
        for record in dump:
            if isinstance(record, ARecord):
                if record.reverse_ptr:
                    reverse = record.reverse_ptr
                else:
                    reverse = record.fqdn

                # Mind the dot!
                result.append("%s.\tIN\tA\t%s" % (record.fqdn, record.ip))
                result.append("%s.\tIN\tPTR\t%s." % (inaddr_ptr(record.ip),
                                                     reverse))
            elif isinstance(record, ReservedName):
                pass
            elif isinstance(record, Alias):
                # Mind the dot!
                result.append("%s.\tIN\tCNAME\t%s." % (record.fqdn,
                                                       record.target.fqdn))
            elif isinstance(record, SrvRecord):
                result.append("%s.\tIN\tSRV\t%d %d %d %s." % (record.fqdn,
                                                              record.priority,
                                                              record.weight,
                                                              record.port,
                                                              record.target.fqdn))
        return "\n".join(result)

    def format_djb(self, dump):
        result = []
        for record in dump:
            if isinstance(record, ARecord):
                if record.reverse_ptr:
                    result.append("+%s:%s" % (record.fqdn, record.ip))
                    result.append("^%s:%s" % (inaddr_ptr(record.ip),
                                              record.reverse_ptr))
                else:
                    result.append("=%s:%s" % (record.fqdn, record.ip))
            elif isinstance(record, ReservedName):
                pass
            elif isinstance(record, Alias):
                result.append("C%s:%s" % (record.fqdn, record.target.fqdn))
            elif isinstance(record, SrvRecord):
                # djbdns does not have native support for SRV records
                result.append(":%s:33:%s%s%s%s" % (record.fqdn,
                                                   octal16(record.priority),
                                                   octal16(record.weight),
                                                   octal16(record.port),
                                                   nstr(record.target.fqdn)))
        return "\n".join(result)


ObjectFormatter.handlers[DnsDump] = DnsDumpFormatter()
