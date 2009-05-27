# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add dns_domain`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.dns_domain import get_dns_domain
from aquilon.server.processes import DSDBRunner
from aquilon.aqdb.model import System


class CommandDelDnsDomain(BrokerCommand):

    required_parameters = ["dns_domain"]

    def render(self, session, dns_domain, **arguments):
        dbdns_domain = get_dns_domain(session, dns_domain)

        dbsystem = session.query(System).filter_by(
                dns_domain=dbdns_domain).first()
        if dbsystem:
            raise ArgumentError("DNS domain %s cannot be deleted while still in use." % dns_domain)

        session.delete(dbdns_domain)
        session.flush()

        dsdb_runner = DSDBRunner()
        dsdb_runner.delete_dns_domain(dns_domain)

        return


