# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq cat --service`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.templates.service import (PlenaryService,
                                              PlenaryServiceClientDefault)


class CommandCatService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, default, **kwargs):
        dbservice = get_service(session, service)
        if default:
            plenary_info = PlenaryServiceClientDefault(dbservice)
        else:
            plenary_info = PlenaryService(dbservice)
        return plenary_info.read(self.config.get("broker", "plenarydir"))


