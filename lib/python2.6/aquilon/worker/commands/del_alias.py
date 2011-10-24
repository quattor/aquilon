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
"""Contains the logic for `aq del alias`."""


from aquilon.exceptions_ import ArgumentError, ProcessException
from aquilon.aqdb.model import DnsEnvironment, Alias, ReservedName
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.dns import delete_dns_record
from aquilon.worker.processes import DSDBRunner


class CommandDelAlias(BrokerCommand):

    required_parameters = ["fqdn"]

    def render(self, session, logger, fqdn, dns_environment, **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)
        dbdns_rec = Alias.get_unique(session, fqdn=fqdn,
                                     dns_environment=dbdns_env, compel=True)
        domain = dbdns_rec.fqdn.dns_domain.name

        old_target = dbdns_rec.target
        target_is_restricted = old_target.dns_domain.restricted
        delete_dns_record(dbdns_rec)
        delete_target_if_needed(session, old_target)

        session.flush()

        if dbdns_env.is_default and domain == "ms.com" and not target_is_restricted:
            dsdb_runner = DSDBRunner(logger=logger)
            try:
                dsdb_runner.del_alias(fqdn)
            except ProcessException, e:
                raise ArgumentError("Could not delete alias from DSDB: %s" % e)

        return


def delete_target_if_needed(session, dbtarget):
    if not dbtarget.dns_domain.restricted:
        return

    # Make sure the original alias is gone before we reference alias_cnt below
    session.flush()

    delete_target_fqdn = True
    for rec in dbtarget.dns_records:
        if not isinstance(rec, ReservedName) or rec.alias_cnt > 0:
            delete_target_fqdn = False
        else:
            session.delete(rec)
    if delete_target_fqdn:
        session.flush()
        session.delete(dbtarget)
