# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""DNS Domain formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.net.dns_domain import DnsDomain


class DnsDomainFormatter(ObjectFormatter):
    def format_raw(self, dns_domain, indent=""):
        details = [ indent + "DNS Domain: %s" % dns_domain.name ]
        if dns_domain.comments:
            details.append(indent + "  Comments: %s" % dns_domain.comments)
        return "\n".join(details)

    def format_csv(self, dns_domain):
        return "%s,%s" % (dns_domain.name, dns_domain.comments or "")


class DNSDomainList(list):
    """By convention, holds DnsDomain objects."""
    pass


class DNSDomainListFormatter(ListFormatter):

    protocol = "aqddnsdomains_pb2"

    def format_proto(self, dns_domain_list):
        dns_domain_list_msg = \
                self.loaded_protocols[self.protocol].DNSDomainList()
        for dns_domain in dns_domain_list:
            self.add_dns_domain_msg(dns_domain_list_msg.dns_domains.add(),
                                    dns_domain)
        return dns_domain_list_msg.SerializeToString()

ObjectFormatter.handlers[DnsDomain] = DnsDomainFormatter()
ObjectFormatter.handlers[DNSDomainList] = DNSDomainListFormatter()


