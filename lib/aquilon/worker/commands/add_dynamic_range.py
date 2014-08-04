# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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

from ipaddr import IPv4Address

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (DynamicStub, ARecord, DnsDomain, Fqdn,
                                AddressAssignment, NetworkEnvironment,
                                DnsEnvironment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers.interface import check_ip_restrictions
from aquilon.worker.dbwrappers.location import get_default_dns_domain
from aquilon.worker.processes import DSDBRunner


class CommandAddDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip"]

    def render(self, session, logger, startip, endip, dns_domain, prefix,
               **arguments):
        if not prefix:
            prefix = 'dynamic'
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        dbdns_env = DnsEnvironment.get_unique_or_default(session)
        startnet = get_net_id_from_ip(session, startip, dbnet_env)
        endnet = get_net_id_from_ip(session, endip, dbnet_env)
        if startnet != endnet:
            raise ArgumentError("IP addresses %s (%s) and %s (%s) must be on "
                                "the same subnet." %
                                (startip, startnet.ip, endip, endnet.ip))

        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbdns_domain = get_default_dns_domain(startnet.location)

        # Lock order: DNS domain, network
        dbdns_domain.lock_row()
        startnet.lock_row()

        q = session.query(AddressAssignment.ip)
        q = q.filter_by(network=startnet)
        q = q.filter(AddressAssignment.ip >= startip)
        q = q.filter(AddressAssignment.ip <= endip)
        q = q.order_by(AddressAssignment.ip)
        conflicts = q.all()
        if conflicts:
            raise ArgumentError("Cannot allocate the address range because the "
                                "following IP addresses are already in use:\n" +
                                ", ".join([str(c.ip) for c in conflicts]))

        # No filtering on DNS environment. If an address is dynamic in one
        # environment, it should not be considered static in a different
        # environment.
        q = session.query(ARecord)
        q = q.filter_by(network=startnet)
        q = q.filter(ARecord.ip >= startip)
        q = q.filter(ARecord.ip <= endip)
        q = q.order_by(ARecord.ip)
        conflicts = q.all()
        if conflicts:
            raise ArgumentError("Cannot allocate the address range because the "
                                "following DNS records already exist:\n" +
                                "\n".join([format(c, "a") for c in conflicts]))

        dsdb_runner = DSDBRunner(logger=logger)
        with session.no_autoflush:
            for ipint in range(int(startip), int(endip) + 1):
                ip = IPv4Address(ipint)
                check_ip_restrictions(startnet, ip)
                name = "%s-%s" % (prefix, str(ip).replace('.', '-'))
                dbfqdn = Fqdn.get_or_create(session, name=name,
                                            dns_domain=dbdns_domain,
                                            dns_environment=dbdns_env,
                                            preclude=True)
                dbdynamic_stub = DynamicStub(fqdn=dbfqdn, ip=ip, network=startnet)
                session.add(dbdynamic_stub)
                dsdb_runner.add_host_details(dbfqdn, ip)

        session.flush()
        # This may take some time if the range is big, so be verbose
        dsdb_runner.commit_or_rollback("Could not add addresses to DSDB",
                                       verbose=True)

        return
