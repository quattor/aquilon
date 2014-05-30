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

from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (ARecord, DynamicStub, DnsEnvironment,
                                NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.processes import DSDBRunner
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["dns_environment"]

    def render(self, session, logger, fqdn, ip, dns_environment, network_environment, **arguments):

        if network_environment:
            if not isinstance(network_environment, NetworkEnvironment):
                network_environment = NetworkEnvironment.get_unique_or_default(session,
                                                                               network_environment)
            if not dns_environment:
                dns_environment = network_environment.dns_environment

        dbdns_env = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)

        # We can't use get_unique() here, since we always want to filter by
        # DNS environment, even if no FQDN was given
        q = session.query(ARecord)
        if ip:
            q = q.filter_by(ip=ip)
        q = q.join(ARecord.fqdn)
        q = q.options(contains_eager('fqdn'))
        q = q.filter_by(dns_environment=dbdns_env)
        if fqdn:
            (name, dbdns_domain) = parse_fqdn(session, fqdn)
            q = q.filter_by(name=name)
            q = q.filter_by(dns_domain=dbdns_domain)
        try:
            dbaddress = q.one()
        except NoResultFound:
            parts = []
            if fqdn:
                parts.append(fqdn)
            if ip:
                parts.append("ip %s" % ip)
            raise NotFoundException("DNS Record %s not found." %
                                    ", ".join(parts))
        except MultipleResultsFound:
            parts = []
            if fqdn:
                parts.append(fqdn)
            if ip:
                parts.append("ip %s" % ip)
            raise NotFoundException("DNS Record %s is not unique." %
                                    ", ".join(parts))

        dbaddress.network.lock_row()

        if dbaddress.hardware_entity:
            raise ArgumentError("DNS Record {0:a} is the primary name of "
                                "{1:l}, therefore it cannot be "
                                "deleted.".format(dbaddress,
                                                  dbaddress.hardware_entity))

        if dbaddress.service_address:
            # TODO: print the holder object
            raise ArgumentError("DNS Record {0:a} is used as a service "
                                "address, therefore it cannot be deleted."
                                .format(dbaddress))

        if isinstance(dbaddress, DynamicStub):
            raise ArgumentError("DNS Record {0:a} is reserved for dynamic "
                                "DHCP, use del_dynamic_range to delete it."
                                .format(dbaddress))

        # Do not allow deleting the DNS record if the IP address is still in
        # use - except if there are other DNS records having the same
        # address
        if dbaddress.assignments:
            last_use = []
            for addr in dbaddress.assignments:
                if len(addr.dns_records) == 1:
                    last_use.append(addr)
            if last_use:
                users = " ,".join([format(addr.interface, "l") for addr in
                                   last_use])
                raise ArgumentError("IP address %s is still in use by %s." %
                                    (ip, users))
        ip = dbaddress.ip
        old_fqdn = str(dbaddress.fqdn)
        old_comments = dbaddress.comments
        delete_dns_record(dbaddress)
        session.flush()

        if dbdns_env.is_default:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.delete_host_details(old_fqdn, ip,
                                            comments=old_comments)
            dsdb_runner.commit_or_rollback()

        return
