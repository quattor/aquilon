# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.

from sqlalchemy.orm import contains_eager
from sqlalchemy.orm.exc import NoResultFound, MultipleResultsFound

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (ARecord, Fqdn, DnsEnvironment,
                                NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.worker.locks import DeleteKey
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

        with DeleteKey("system", logger=logger):
            # We can't use get_unique() here, since we always want to filter by
            # DNS environment, even if no FQDN was given
            q = session.query(ARecord)
            if ip:
                q = q.filter_by(ip=ip)
            q = q.join(Fqdn)
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

            # Do not allow deleting the DNS record if the IP address is still in
            # use - except if there are other DNS records having the same
            # address
            if dbaddress.assignments:
                last_use = []
                # FIXME: race condition here, we should use
                # SELECT ... FOR UPDATE
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
