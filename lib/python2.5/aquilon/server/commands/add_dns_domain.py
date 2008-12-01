# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add dns_domain`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.net.dns_domain import DnsDomain
from aquilon.server.processes import DSDBRunner


class CommandAddDnsDomain(BrokerCommand):

    required_parameters = ["dns_domain"]

    def render(self, session, dns_domain, comments, **arguments):
        if session.query(DnsDomain).filter_by(name=dns_domain).first():
            raise ArgumentError("DNS domain %s already exists." % dns_domain)

        dbdns_domain = DnsDomain(name=dns_domain, comments=comments)
        session.save(dbdns_domain)
        session.flush()
        session.refresh(dbdns_domain)

        dsdb_runner = DSDBRunner()
        dsdb_runner.add_dns_domain(dbdns_domain.name, comments)

        return


