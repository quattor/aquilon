# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq compile`."""


from aquilon.server.broker import (add_transaction, az_check, BrokerCommand)
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.hw.machine import Machine
from twisted.python import log
from aquilon.server.templates.domain import TemplateDomain
from aquilon.aqdb.sy.domain import Domain
from aquilon.exceptions_ import NotFoundException


class CommandCompile(BrokerCommand):

    required_parameters = ["domain"]

    @az_check
    def render(self, session, domain, user, **arguments):
        d = session.query(Domain).filter_by(name=domain).all()
        if (len(d) != 1):
            raise NotFoundException("Domain '%s' not found"%domain)
        dom = TemplateDomain()
        return dom.compile(session, d[0], user)


