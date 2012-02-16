# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011,2012  Contributor
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
"""Contains the logic for `aq del srv record`."""


from aquilon.exceptions_ import NotFoundException
from aquilon.aqdb.model import SrvRecord, Fqdn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record


class CommandDelSrvRecord(BrokerCommand):

    required_parameters = ["service", "protocol", "dns_domain"]

    def render(self, session, service, protocol, dns_domain, target,
               dns_environment, **kwargs):
        name = "_%s._%s" % (service.strip().lower(), protocol.strip().lower())
        dbfqdn = Fqdn.get_unique(session, name=name, dns_domain=dns_domain,
                                 dns_environment=dns_environment)
        if target:
            dbtarget = Fqdn.get_unique(session, target, compel=True)
        else:
            dbtarget = None

        rrs = []
        if dbfqdn:
            for rr in dbfqdn.dns_records:
                if not isinstance(rr, SrvRecord):  # pragma: no cover
                    # This case can't happen right now. Maybe one day if we
                    # add support for DNSSEC...
                    continue
                if dbtarget and rr.target != dbtarget:
                    continue
                rrs.append(rr)

        if not rrs:
            if dbtarget:
                msg = ", with target %s" % dbtarget.fqdn
            else:
                msg = ""
            raise NotFoundException("%s for service %s, protocol %s in DNS "
                                    "domain %s%s not found." %
                                    (SrvRecord._get_class_label(), service,
                                     protocol, dns_domain, msg))

        map(delete_dns_record, rrs)
        session.flush()

        return
