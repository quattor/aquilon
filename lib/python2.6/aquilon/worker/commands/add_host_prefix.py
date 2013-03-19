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
"""Contains a wrapper for `aq add host --prefix`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_host import CommandAddHost
from aquilon.worker.dbwrappers.search import search_next
from aquilon.aqdb.model import Machine, DnsDomain, Fqdn
from aquilon.aqdb.column_types import AqStr


class CommandAddHostPrefix(CommandAddHost):

    required_parameters = ["prefix", "machine", "archetype"]

    def render(self, session, logger, prefix, dns_domain, hostname, machine,
               **args):
        if dns_domain:
            dbdns_domain = DnsDomain.get_unique(session, dns_domain,
                                                compel=True)
        else:
            dbmachine = Machine.get_unique(session, machine, compel=True)
            dbdns_domain = None
            loc = dbmachine.location
            while loc and not dbdns_domain:
                dbdns_domain = loc.default_dns_domain
                loc = loc.parent

            if not dbdns_domain:
                raise ArgumentError("There is no default DNS domain configured "
                                    "for the machine's location. Please "
                                    "specify --dns_domain.")

        # Lock the DNS domain to prevent the same name generated for
        # simultaneous requests
        dbdns_domain.lock_row()

        prefix = AqStr.normalize(prefix)
        result = search_next(session=session, cls=Fqdn, attr=Fqdn.name,
                             value=prefix, dns_domain=dbdns_domain,
                             start=None, pack=None)
        hostname = "%s%d.%s" % (prefix, result, dbdns_domain)

        CommandAddHost.render(self, session, logger, hostname=hostname,
                              machine=machine, **args)

        logger.info("Selected host name %s" % hostname)
        self.audit_result(session, 'hostname', hostname, **args)
        return hostname
