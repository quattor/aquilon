# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq add router`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import (RouterAddress, Building, ARecord, Fqdn,
                                NetworkEnvironment)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddRouter(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, dbuser,
               fqdn, building, ip, network_environment, comments, **arguments):
        dbnet_env = NetworkEnvironment.get_unique_or_default(session,
                                                             network_environment)
        self.az.check_network_environment(dbuser, dbnet_env)

        if building:
            dbbuilding = Building.get_unique(session, building, compel=True)
        else:
            dbbuilding = None

        (short, dbdns_domain) = parse_fqdn(session, fqdn)
        dbfqdn = Fqdn.get_or_create(session, name=short,
                                    dns_domain=dbdns_domain,
                                    dns_environment=dbnet_env.dns_environment)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip, dbnet_env)
            dbdns_rec = ARecord.get_or_create(session, fqdn=dbfqdn, ip=ip,
                                              network=dbnetwork)
        else:
            dbdns_rec = ARecord.get_unique(session, dbfqdn, compel=True)
            ip = dbdns_rec.ip
            dbnetwork = dbdns_rec.network

        assert ip in dbnetwork.network, "IP %s is outside network %s" % (ip,
                                                                         dbnetwork.ip)

        if ip in dbnetwork.router_ips:
            raise ArgumentError("IP address {0} is already present as a router "
                                "for {1:l}.".format(ip, dbnetwork))

        # Policy checks are valid only for internal networks
        if dbnetwork.is_internal:
            if ip >= dbnetwork.first_usable_host or \
               int(ip) - int(dbnetwork.ip) in dbnetwork.reserved_offsets:
                raise ArgumentError("IP address {0} is not a valid router address "
                                    "on {1:l}.".format(ip, dbnetwork))

        dbnetwork.routers.append(RouterAddress(ip=ip, location=dbbuilding,
                                               dns_environment=dbdns_rec.fqdn.dns_environment,
                                               comments=comments))
        session.flush()

        # TODO: update the templates of Zebra hosts on the network

        return
