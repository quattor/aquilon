#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show service --service`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandShowServiceService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, service, instance, **arguments):
        dbservice = get_service(session, service)
        if not instance:
            return dbservice
        return get_service_instance(session, dbservice, instance)


#if __name__=='__main__':
