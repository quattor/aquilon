#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show service --service`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.system import get_system
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.server.formats.service_instance import ServiceInstanceList


class CommandShowServiceService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    @format_results
    def render(self, session, service, instance, server, **arguments):
        dbservice = get_service(session, service)
        if not instance and not server:
            return dbservice
        q = session.query(ServiceInstance).filter_by(service=dbservice)
        if instance:
            q = q.filter_by(name=instance)
        if server:
            dbsystem = get_system(session, server)
            q = q.join('servers').filter_by(system=dbsystem)
        return ServiceInstanceList(q.all())


#if __name__=='__main__':
