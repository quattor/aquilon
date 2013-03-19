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

from aquilon.aqdb.model.network_environment import get_net_dns_env
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.dns import (grab_address,
                                           set_reverse_ptr)
from aquilon.worker.dbwrappers.interface import generate_ip
from aquilon.worker.processes import DSDBRunner


class CommandAddAddressDNSEnvironment(BrokerCommand):

    required_parameters = ["fqdn", "dns_environment"]

    def render(self, session, logger, fqdn, dns_environment,
               network_environment, reverse_ptr, comments, **arguments):
        dbnet_env, dbdns_env = get_net_dns_env(session, network_environment,
                                               dns_environment)
        audit_results = []
        ip = generate_ip(session, logger, compel=True, dbinterface=None,
                         network_environment=dbnet_env,
                         audit_results=audit_results, **arguments)
        # TODO: add allow_multi=True
        dbdns_rec, newly_created = grab_address(session, fqdn, ip, dbnet_env,
                                                dbdns_env, comments=comments,
                                                preclude=True)

        if reverse_ptr:
            set_reverse_ptr(session, logger, dbdns_rec, reverse_ptr)

        session.flush()

        if dbdns_rec.fqdn.dns_environment.is_default:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.add_host_details(dbdns_rec.fqdn, ip, comments=comments)
            dsdb_runner.commit_or_rollback("Could not add address to DSDB")

        for name, value in audit_results:
            self.audit_result(session, name, value, **arguments)
        return
