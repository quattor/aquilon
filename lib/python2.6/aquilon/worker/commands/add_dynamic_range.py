# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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

from ipaddr import IPv4Address

from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (DynamicStub, ARecord, DnsDomain, Fqdn,
                                AddressAssignment, NetworkEnvironment)
from aquilon.aqdb.model.network import get_net_id_from_ip
from aquilon.exceptions_ import ArgumentError
from aquilon.worker.dbwrappers.interface import check_ip_restrictions
from aquilon.worker.processes import DSDBRunner


class CommandAddDynamicRange(BrokerCommand):

    required_parameters = ["startip", "endip", "dns_domain"]

    def render(self, session, logger, startip, endip, dns_domain, prefix,
               **arguments):
        if not prefix:
            prefix = 'dynamic'
        dbnet_env = NetworkEnvironment.get_unique_or_default(session)
        startnet = get_net_id_from_ip(session, startip, dbnet_env)
        endnet = get_net_id_from_ip(session, endip, dbnet_env)
        if startnet != endnet:
            raise ArgumentError("IP addresses %s (%s) and %s (%s) must be on "
                                "the same subnet." %
                                (startip, startnet.ip, endip, endnet.ip))
        dbdns_domain = DnsDomain.get_unique(session, dns_domain, compel=True)

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
        for ipint in range(int(startip), int(endip) + 1):
            ip = IPv4Address(ipint)
            check_ip_restrictions(startnet, ip)
            name = "%s-%s" % (prefix, str(ip).replace('.', '-'))
            dbfqdn = Fqdn.get_or_create(session, name=name,
                                        dns_domain=dbdns_domain, preclude=True)
            dbdynamic_stub = DynamicStub(fqdn=dbfqdn, ip=ip, network=startnet)
            session.add(dbdynamic_stub)
            dsdb_runner.add_host_details(dbfqdn, ip)

        session.flush()
        # This may take some time if the range is big, so be verbose
        dsdb_runner.commit_or_rollback("Could not add addresses to DSDB",
                                       verbose=True)

        return
