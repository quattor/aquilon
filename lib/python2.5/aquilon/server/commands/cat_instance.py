#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq cat --service --instance`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.templates.service import (PlenaryServiceInstance,
                                        PlenaryServiceInstanceClientDefault)


class CommandCatService(BrokerCommand):

    required_parameters = ["service", "instance"]

    def render(self, session, service, instance, default, **kwargs):
        dbservice = get_service(session, service)
        dbsi = get_service_instance(session, dbservice, instance)
        if default:
            plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbsi)
        else:
            plenary_info = PlenaryServiceInstance(dbservice, dbsi)
        return plenary_info.read(self.config.get("broker", "plenarydir"))


#if __name__=='__main__':
