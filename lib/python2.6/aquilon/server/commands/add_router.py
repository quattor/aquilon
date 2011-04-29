# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import RouterAddress, Building, ARecord, Fqdn
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.aqdb.model.network import get_net_id_from_ip


class CommandAddRouter(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, fqdn, building, ip, comments, **arguments):
        if building:
            dbbuilding = Building.get_unique(session, building, compel=True)
        else:
            dbbuilding = None

        (short, dbdns_domain) = parse_fqdn(session, fqdn)
        dbfqdn = Fqdn.get_or_create(session, name=short,
                                    dns_domain=dbdns_domain)
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)
            dbdns_rec = ARecord.get_or_create(session, fqdn=dbfqdn, ip=ip,
                                              network=dbnetwork)
        else:
            dbdns_rec = ARecord.get_unique(session, dbfqdn, compel=True)
            ip = dbdns_rec.ip
            dbnetwork = dbdns_rec.network

        if ip in dbnetwork.router_ips:
            raise ArgumentError("IP address {0} is already present as a router "
                                "for {1:l}.".format(ip, dbnetwork))

        if ip <= dbnetwork.ip or ip >= dbnetwork.first_usable_host or \
           int(ip) - int(dbnetwork.ip) in dbnetwork.reserved_offsets:
            raise ArgumentError("IP address {0} is not a valid router address "
                                "on {1:l}.".format(ip, dbnetwork))

        dbnetwork.routers.append(RouterAddress(ip=ip, location=dbbuilding,
                                               dns_environment=dbdns_rec.fqdn.dns_environment,
                                               comments=comments))
        session.flush()

        # TODO: update the templates of Zebra hosts on the network

        return
