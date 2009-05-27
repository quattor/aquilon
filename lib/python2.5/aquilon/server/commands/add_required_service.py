# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add required service`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import ServiceListItem
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.service import get_service


class CommandAddRequiredService(BrokerCommand):

    required_parameters = ["service", "archetype"]

    def render(self, session, service, archetype, comments, **arguments):
        dbarchetype = get_archetype(session, archetype)
        dbservice = get_service(session, service)
        dbsli = ServiceListItem(archetype=dbarchetype, service=dbservice,
                comments=comments)
        session.add(dbsli)
        return


