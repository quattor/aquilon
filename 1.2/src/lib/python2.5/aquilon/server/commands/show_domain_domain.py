#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show domain --domain`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.systems import Domain


class CommandShowDomainDomain(BrokerCommand):

    required_parameters = ["domain"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, domain, **arguments):
        return session.query(Domain).filter_by(name=domain).all()


#if __name__=='__main__':
