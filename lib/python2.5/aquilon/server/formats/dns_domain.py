# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""DNS Domain formatter."""


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.net.dns_domain import DnsDomain


class DnsDomainFormatter(ObjectFormatter):
    def format_raw(self, dns_domain, indent=""):
        details = [ indent + "DNS Domain: %s" % dns_domain.name ]
        if dns_domain.comments:
            details.append(indent + "  Comments: %s" % dns_domain.comments)
        return "\n".join(details)

    def format_csv(self, dns_domain):
        return "%s,%s" % (dns_domain.name, dns_domain.comments or "")

ObjectFormatter.handlers[DnsDomain] = DnsDomainFormatter()


