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
"""Contains the logic for `aq add alias`."""

import socket

from sqlalchemy.orm.exc import NoResultFound

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import (DnsRecord, Alias, Fqdn, DnsEnvironment,
                                ReservedName)
from aquilon.aqdb.model.dns_domain import parse_fqdn
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.processes import DSDBRunner


class CommandAddAlias(BrokerCommand):

    required_parameters = ["fqdn", "target"]

    def render(self, session, logger, fqdn, dns_environment, target, comments,
               **kwargs):
        dbdns_env = DnsEnvironment.get_unique_or_default(session,
                                                         dns_environment)

        dbfqdn = Fqdn.get_or_create(session, dns_environment=dbdns_env,
                                    fqdn=fqdn)

        if dbfqdn.dns_domain.restricted:
            raise ArgumentError("{0} is restricted, aliases are not allowed."
                                .format(dbfqdn.dns_domain))

        DnsRecord.get_unique(session, fqdn=dbfqdn, preclude=True)

        dbtarget = create_target_if_needed(session, logger, target, dbdns_env)
        try:
            db_record = Alias(fqdn=dbfqdn, target=dbtarget, comments=comments)
            session.add(db_record)
        except ValueError, err:
            raise ArgumentError(err.message)

        session.flush()

        if dbdns_env.is_default and dbfqdn.dns_domain.name == "ms.com" and \
           not dbtarget.dns_domain.restricted:
            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.add_alias(fqdn, target, comments)
            dsdb_runner.commit_or_rollback("Could not add alias to DSDB")

        return


def create_target_if_needed(session, logger, target, dbdns_env):
    (name, target_domain) = parse_fqdn(session, target)
    q = session.query(Fqdn)
    q = q.filter_by(dns_environment=dbdns_env)
    q = q.filter_by(dns_domain=target_domain)
    q = q.filter_by(name=name)
    try:
        dbtarget = q.one()
    except NoResultFound:
        if not target_domain.restricted:
            raise NotFoundException("Target FQDN {0} does not exist in {1:l}."
                                    .format(target, dbdns_env))

        dbtarget = Fqdn(name=name, dns_domain=target_domain,
                        dns_environment=dbdns_env)

        try:
            socket.gethostbyname(dbtarget.fqdn)
        except socket.gaierror, e:
            logger.warning("WARNING: Will create alias for target {0.fqdn!s}, "
                           "but trying to resolve it resulted in an error: "
                           "{1.strerror}.".format(dbtarget, e))

        session.add(dbtarget)
        dbtarget_rec = ReservedName(fqdn=dbtarget)
        session.add(dbtarget_rec)

    return dbtarget
