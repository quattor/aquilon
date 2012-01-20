# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2010,2011  Contributor
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

from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import DnsRecord, ARecord, DnsEnvironment, Fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.interface import (generate_ip,
                                                 check_ip_restrictions)
from aquilon.worker.processes import DSDBRunner


class CommandAddAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["fqdn", "dns_environment"]

    def render(self, session, logger, fqdn, dns_environment, comments,
               **arguments):
        dbdns_env = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)

        dbfqdn = Fqdn.get_or_create(session, dns_environment=dbdns_env,
                                    fqdn=fqdn)

        if dbfqdn.dns_domain.restricted:
            raise ArgumentError("{0} is restricted, standalone A records "
                                "are not allowed.".format(dbfqdn.dns_domain))

        DnsRecord.get_unique(session, fqdn=dbfqdn, preclude=True)

        ip = generate_ip(session, compel=True, dbinterface=None, **arguments)
        ipnet = get_net_id_from_ip(session, ip)
        check_ip_restrictions(ipnet, ip)
        dbaddress = ARecord(fqdn=dbfqdn, ip=ip, network=ipnet, comments=comments)
        session.add(dbaddress)

        session.flush()

        if dbdns_env.is_default:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.add_host_details(fqdn=dbaddress.fqdn, ip=dbaddress.ip,
                                             name=None, mac=None)
            except ProcessException, e:
                raise ArgumentError("Could not add address to DSDB: %s" % e)

        return
