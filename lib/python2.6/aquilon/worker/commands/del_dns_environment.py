# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
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
"""Contains the logic for `aq add dns_domain`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import (DnsEnvironment, RouterAddress,
                                AddressAssignment, Fqdn)


class CommandDelDnsEnvironment(BrokerCommand):

    required_parameters = ["dns_environment"]

    def render(self, session, dns_environment, **arguments):
        db_dnsenv = DnsEnvironment.get_unique(session, dns_environment,
                                              compel=True)

        if db_dnsenv.is_default:
            raise ArgumentError("{0} is the default DNS environment, "
                                "therefore it cannot be deleted."
                                .format(db_dnsenv))
        q = session.query(Fqdn)
        q = q.filter_by(dns_environment=db_dnsenv)
        if q.first():
            raise ArgumentError("{0} is still in use by DNS records, and "
                                "cannot be deleted.".format(db_dnsenv))

        q = session.query(RouterAddress)
        q = q.filter_by(dns_environment=db_dnsenv)
        if q.first():
            raise ArgumentError("{0} is still in use by routers, and "
                                "cannot be deleted.".format(db_dnsenv))

        q = session.query(AddressAssignment)
        q = q.filter_by(dns_environment=db_dnsenv)
        if q.first():
            raise ArgumentError("{0} is still in use by address assignments, "
                                "and cannot be deleted.".format(db_dnsenv))

        session.delete(db_dnsenv)
        session.flush()

        return
