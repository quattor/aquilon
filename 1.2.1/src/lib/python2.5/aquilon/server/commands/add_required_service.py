#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add required service`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.svc.service_list_item import ServiceListItem
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.service import get_service


class CommandAddRequiredService(BrokerCommand):

    required_parameters = ["service", "archetype"]

    @add_transaction
    @az_check
    def render(self, session, service, archetype, comments, **arguments):
        dbarchetype = get_archetype(session, archetype)
        dbservice = get_service(session, service)
        dbsli = ServiceListItem(dbarchetype, dbservice, comments=comments)
        session.save_or_update(dbsli)
        return


#if __name__=='__main__':
