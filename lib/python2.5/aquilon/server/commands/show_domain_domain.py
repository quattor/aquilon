# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show domain --domain`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Domain
from aquilon.exceptions_ import NotFoundException


class CommandShowDomainDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, domain, **arguments):
        dlist = session.query(Domain).filter_by(name=domain).all() 
        if (len(dlist) != 1):
            raise NotFoundException("domain '%s' is unknown"%domain)
        return dlist


