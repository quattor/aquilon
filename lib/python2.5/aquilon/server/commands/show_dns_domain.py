# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show dns_domain --all`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import DnsDomain
from aquilon.server.formats.dns_domain import DNSDomainList


class CommandShowDnsDomain(BrokerCommand):

    required_parameters = []

    def render(self, session, **arguments):
        return DNSDomainList(session.query(DnsDomain).all())


