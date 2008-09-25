#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq search system`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.formats.system import SimpleSystemList
from aquilon.aqdb.sy.system import System
from aquilon.server.dbwrappers.system import parse_system
from aquilon.server.dbwrappers.dns_domain import get_dns_domain
from aquilon.server.dbwrappers.network import get_network_byip


class CommandSearchSystem(BrokerCommand):

    required_parameters = []

    @add_transaction
    @az_check
    @format_results
    def render(self, session, fqdn, dnsdomain, shortname, ip, networkip,
               mac, fullinfo, **arguments):
        q = session.query(System)
        if fqdn:
            (short, dbdns_domain) = parse_system(session, fqdn)
            q = q.filter_by(name=short, dns_domain=dbdns_domain)
        if dnsdomain:
            dbdns_domain = get_dns_domain(session, dnsdomain)
            q = q.filter_by(dns_domain=dbdns_domain)
        if shortname:
            q = q.filter_by(name=shortname)
        if ip:
            q = q.filter_by(ip=ip)
        if networkip:
            dbnetwork = get_network_byip(session, networkip)
            q = q.filter_by(network=dbnetwork)
        if mac:
            q = q.filter_by(mac=mac)
        if fullinfo:
            return q.all()
        return SimpleSystemList(q.all())


#if __name__=='__main__':
