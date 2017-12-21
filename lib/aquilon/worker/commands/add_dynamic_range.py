# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014,2015,2016,2017  Contributor
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

from ipaddress import ip_address, IPv4Network

from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.model import (DynamicStub, ARecord, DnsDomain, Fqdn,
                                ReservedName, AddressAssignment)
from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import check_ip_restrictions
from aquilon.worker.dbwrappers.location import get_default_dns_domain
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandAddDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip"]

    def render(self, session, logger, startip, endip, dns_domain,
               prefix, exporter, user, justification, reason, **arguments):
        if not prefix:
            prefix = 'dynamic'
        dbnet_env, dbdns_env = get_net_dns_env(session)
        startnet = get_net_id_from_ip(session, startip, dbnet_env)
        endnet = get_net_id_from_ip(session, endip, dbnet_env)
        if startnet != endnet:
            raise ArgumentError("IP addresses %s (%s) and %s (%s) must be on "
                                "the same subnet." %
                                (startip, startnet.network_address,
                                 endip, endnet.network_address))

        if not isinstance(startnet.network, IPv4Network):
            raise UnimplementedError("Registering dynamic DHCP ranges is not "
                                     "supported on IPv6 networks.")

        # Validate ChangeManagement
        cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
        cm.consider(startnet)
        cm.validate()

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
                                ", ".join(sorted(str(c.ip) for c in conflicts)))

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
                                "\n".join(format(c, "a") for c in conflicts))

        dsdb_runner = DSDBRunner(logger=logger)
        with session.no_autoflush:
            for ipint in range(int(startip), int(endip) + 1):
                ip = ip_address(ipint)
                check_ip_restrictions(startnet, ip)
                name = "%s-%s" % (prefix, str(ip).replace('.', '-'))
                dbfqdn = Fqdn.get_or_create(session, name=name,
                                            dns_domain=dbdns_domain,
                                            dns_environment=dbdns_env,
                                            preclude=True)
                dbdynamic_stub = DynamicStub(fqdn=dbfqdn, ip=ip, network=startnet)
                session.add(dbdynamic_stub)


                if exporter:
                    if any(
                            dr != dbdynamic_stub and
                            not isinstance(dr, ReservedName)
                            for dr in dbfqdn.dns_records):
                        exporter.update(dbfqdn)
                    else:
                        exporter.create(dbfqdn)

                dsdb_runner.add_host_details(dbfqdn, ip)

        session.flush()
        # This may take some time if the range is big, so be verbose
        dsdb_runner.commit_or_rollback("Could not add addresses to DSDB",
                                       verbose=True)

        return
