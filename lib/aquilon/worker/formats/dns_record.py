# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008-2015,2017,2019  Contributor
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

import struct

from ipaddress import IPv4Address

from aquilon.exceptions_ import ProtocolError
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import (DnsRecord, DynamicStub, ARecord, Alias,
                                AddressAlias, ReservedName, SrvRecord, Fqdn)


class DnsRecordFormatter(ObjectFormatter):
    template_raw = "dns_record.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name, None)


class ARecordFormatter(ObjectFormatter):
    template_raw = "a_record.mako"

    def csv_fields(self, dns_record):
        if isinstance(dns_record.ip, IPv4Address):
            rrtype = "A"
        else:
            rrtype = "AAAA"

        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               rrtype, dns_record.ip, dns_record.reverse_ptr)

    def fill_proto(self, dns_record, skeleton, embedded=True, indirect_attrs=True):
        skeleton.rrtype = (
            skeleton.A
            if isinstance(dns_record.ip, IPv4Address)
            else skeleton.AAAA
        )
        skeleton.target = str(dns_record.ip)
        skeleton.target_network_environment_name = \
            dns_record.network.network_environment.name
        if dns_record.ttl is not None:
            skeleton.ttl = dns_record.ttl


class AliasFormatter(ObjectFormatter):
    template_raw = "alias.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               'CNAME', dns_record.target)

    def fill_proto(self, dns_record, skeleton, embedded=True, indirect_attrs=True):
        skeleton.rrtype = skeleton.CNAME
        skeleton.target = str(dns_record.target)
        skeleton.target_environment_name = dns_record.target.dns_environment.name
        if dns_record.ttl is not None:
            skeleton.ttl = dns_record.ttl


class SrvRecordFormatter(ObjectFormatter):
    template_raw = "srv_record.mako"

    def csv_fields(self, dns_record):
        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               'SRV', dns_record.priority, dns_record.weight,
               dns_record.target, dns_record.port)

    def fill_proto(self, dns_record, skeleton, embedded=True, indirect_attrs=True):
        skeleton.rrtype = skeleton.SRV
        skeleton.target = str(dns_record.target)
        skeleton.target_environment_name = dns_record.target.dns_environment.name
        skeleton.priority = dns_record.priority
        skeleton.port = dns_record.port
        skeleton.weight = dns_record.weight
        if dns_record.ttl is not None:
            skeleton.ttl = dns_record.ttl


class AddressAliasFormatter(ObjectFormatter):
    template_raw = "address_alias.mako"

    def csv_fields(self, dns_record):
        if isinstance(dns_record.target_ip, IPv4Address):
            rrtype = "A"
        else:
            rrtype = "AAAA"

        yield (dns_record.fqdn, dns_record.fqdn.dns_environment.name,
               rrtype, dns_record.target_ip)

    def fill_proto(self, dns_record, skeleton, embedded=True, indirect_attrs=True):
        skeleton.rrtype = (
            skeleton.A
            if isinstance(dns_record.target_ip, IPv4Address)
            else skeleton.AAAA
        )
        skeleton.target = str(dns_record.target_ip)
        skeleton.target_network_environment_name = \
            dns_record.target_network.network_environment.name
        if dns_record.ttl is not None:
            skeleton.ttl = dns_record.ttl


# The DnsRecord entry should never get invoked, we always have a subclass.
ObjectFormatter.handlers[DnsRecord] = DnsRecordFormatter()
ObjectFormatter.handlers[ReservedName] = DnsRecordFormatter()

ObjectFormatter.handlers[DynamicStub] = ARecordFormatter()
ObjectFormatter.handlers[ARecord] = ARecordFormatter()

ObjectFormatter.handlers[Alias] = AliasFormatter()
ObjectFormatter.handlers[AddressAlias] = AddressAliasFormatter()

ObjectFormatter.handlers[SrvRecord] = SrvRecordFormatter()


def inaddr_ptr(ip):
    octets = str(ip).split('.')
    octets.reverse()
    return "%s.in-addr.arpa" % '.'.join(octets)


def in6addr_ptr(ip):
    octets = list(struct.unpack("B" * 16, ip.packed))
    octets.reverse()
    # This may not look intuitive, but this was the fastest variant I could come
    # up with - improvements are welcome :-)
    return "".join(format((octet & 0xf) << 4 | (octet >> 4), "02x")
                   for octet in octets).replace("", ".")[1:-1] + ".ip6.arpa"


def octal16(value):
    return "\\%03o\\%03o" % (value >> 8, value & 0xff)


def str8(text):
    return "\\%03o" % len(text) + text.replace(':', '\\072')


def nstr(text):
    return "".join(str8(p) for p in (text + ".").split('.'))


def ip6(ip):
    octets = struct.unpack("B" * 16, ip.packed)
    return "\\" + "\\".join(format(octet, "03o") for octet in octets)


def process_reverse_ptr(container, record):
    # If this is not an A record, nothing to do
    if not isinstance(record, ARecord):
        return

    # If there is a specific reverse to be used, use it,
    # or else fall back on the record FQDN
    target = record.reverse_ptr
    if target is None:
        target = record.fqdn

    # Prepare the record for which the FQDN will be the
    # arpa representation of the IP address
    reverse = container.add()
    reverse.fqdn = (
        inaddr_ptr(record.ip)
        if isinstance(record.ip, IPv4Address)
        else in6addr_ptr(record.ip)
    )
    reverse.environment_name = \
        record.network.network_environment.dns_environment.name

    # Then add the PTR record to the reverse
    ptr_record = reverse.rdata.add()
    ptr_record.rrtype = ptr_record.PTR
    ptr_record.target = str(target)
    ptr_record.target_environment_name = target.dns_environment.name
    if record.ttl is not None:
        ptr_record.ttl = record.ttl


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

    def format_raw(self, dump, indent="", embedded=True, indirect_attrs=True):
        result = []
        # The output is not the most readable as we don't make use of $ORIGIN,
        # but BIND should be able to digest it
        for record in dump:
            if record.ttl is not None:
                ttl = "\t" + str(record.ttl)
            else:
                ttl = ''

            if isinstance(record, ARecord):
                reverse = record.reverse_ptr or record.fqdn

                # Mind the dot!
                if isinstance(record.ip, IPv4Address):
                    result.append("%s.%s\tIN\tA\t%s" %
                                  (record.fqdn, ttl, record.ip))
                    result.append("%s.%s\tIN\tPTR\t%s." %
                                  (inaddr_ptr(record.ip), ttl, reverse))
                else:
                    result.append("%s.%s\tIN\tAAAA\t%s" %
                                  (record.fqdn, ttl, record.ip))
                    result.append("%s.%s\tIN\tPTR\t%s." %
                                  (in6addr_ptr(record.ip), ttl, reverse))
            elif isinstance(record, ReservedName):
                pass
            elif isinstance(record, Alias):
                # Mind the dot!
                result.append("%s.%s\tIN\tCNAME\t%s." % (record.fqdn, ttl,
                                                         record.target.fqdn))
            elif isinstance(record, SrvRecord):
                result.append("%s.%s\tIN\tSRV\t%d %d %d %s." % (record.fqdn,
                                                                ttl,
                                                                record.priority,
                                                                record.weight,
                                                                record.port,
                                                                record.target.fqdn))
            elif isinstance(record, AddressAlias):
                if isinstance(record.target_ip, IPv4Address):
                    result.append("%s.%s\tIN\tA\t%s" % (record.fqdn, ttl,
                                                        record.target_ip))
                else:
                    result.append("%s.%s\tIN\tAAAA\t%s" % (record.fqdn, ttl,
                                                           record.target_ip))

        return "\n".join(result)

    def format_djb(self, dump):
        result = []
        for record in dump:
            if record.ttl is not None:
                ttl = ":" + str(record.ttl)
            else:
                ttl = ''

            if isinstance(record, ARecord):
                if isinstance(record.ip, IPv4Address):
                    if record.reverse_ptr:
                        result.append("+%s:%s%s" % (record.fqdn, record.ip, ttl))
                        result.append("^%s:%s%s" % (inaddr_ptr(record.ip),
                                                    record.reverse_ptr, ttl))
                    else:
                        result.append("=%s:%s%s" % (record.fqdn, record.ip, ttl))
                else:
                    result.append(":%s:28:%s%s" % (record.fqdn, ip6(record.ip), ttl))
                    ptr = record.reverse_ptr or record.fqdn
                    result.append("^%s:%s%s" % (in6addr_ptr(record.ip), ptr, ttl))
            elif isinstance(record, ReservedName):
                pass
            elif isinstance(record, Alias):
                result.append("C%s:%s%s" % (record.fqdn, record.target.fqdn, ttl))
            elif isinstance(record, AddressAlias):
                if isinstance(record.target_ip, IPv4Address):
                    result.append("+%s:%s%s" % (record.fqdn, record.target_ip, ttl))
                else:
                    result.append(":%s:28:%s%s" % (record.fqdn,
                                                   ip6(record.target_ip), ttl))
            elif isinstance(record, SrvRecord):
                # djbdns does not have native support for SRV records
                result.append(":%s:33:%s%s%s%s%s" % (record.fqdn,
                                                     octal16(record.priority),
                                                     octal16(record.weight),
                                                     octal16(record.port),
                                                     nstr(record.target.fqdn),
                                                     ttl))

        return "\n".join(result)

    def format_proto(self, dump, container, embedded=True, indirect_attrs=True):
        entry = None
        for record in sorted(
            dump,
            key=lambda r: (str(r.fqdn), r.fqdn.dns_environment.name)
        ):
            if isinstance(record, ReservedName):
                continue

            r_fqdn = str(record.fqdn)
            r_env = record.fqdn.dns_environment.name
            if entry is None or \
                    r_fqdn != entry.fqdn or \
                    r_env != entry.environment_name:
                entry = container.add()
                entry.fqdn = r_fqdn
                entry.environment_name = r_env

            skeleton = entry.rdata.add()
            self.redirect_proto(record, skeleton)

            process_reverse_ptr(container, record)

ObjectFormatter.handlers[DnsDump] = DnsDumpFormatter()


class FqdnFormatter(ObjectFormatter):

    def format_proto(self, result, container, embedded=True, indirect_attrs=True):
        skeleton = container.add()
        skeleton.fqdn = str(result)
        skeleton.environment_name = result.dns_environment.name
        for record in result.dns_records:
            if isinstance(record, ReservedName):
                continue

            r_skeleton = skeleton.rdata.add()
            self.redirect_proto(record, r_skeleton)

            process_reverse_ptr(container, record)

ObjectFormatter.handlers[Fqdn] = FqdnFormatter()
