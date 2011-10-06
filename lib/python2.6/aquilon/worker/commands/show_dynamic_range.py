# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
"""Contains the logic for `aq show dynamic range`."""

from ipaddr import IPv4Address

from aquilon.aqdb.model import DynamicStub, DnsEnvironment
from aquilon.aqdb.model.network import get_net_id_from_ip

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.dynamic_range import DynamicRange


class CommandShowDynamicRange(BrokerCommand):
    def render(self, session, fqdn, ip, dns_environment, **arguments):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        if fqdn:
            dbdns_rec = DynamicStub.get_unique(session, fqdn=fqdn,
                                               dns_environment=dbdns_env,
                                               compel=True)
            dbnetwork = dbdns_rec.network
            ip = dbdns_rec.ip
        if ip:
            dbnetwork = get_net_id_from_ip(session, ip)

        all_stubs = {}
        q = session.query(DynamicStub.ip)
        q = q.filter_by(network=dbnetwork)
        for stub in q:
            all_stubs[int(stub.ip)] = True

        start = int(ip)
        while start > int(dbnetwork.ip) and start - 1 in all_stubs:
            start = start - 1

        end = int(ip)
        while end < int(dbnetwork.broadcast) and end + 1 in all_stubs:
            end = end + 1

        return DynamicRange(dbnetwork, IPv4Address(start), IPv4Address(end))
