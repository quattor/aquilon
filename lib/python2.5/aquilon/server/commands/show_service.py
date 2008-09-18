#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show service`."""

from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service_instance import get_client_service_instances
from aquilon.server.formats.service_instance import ServiceInstanceList
from aquilon.server.formats.service import ServiceList

class CommandShowService(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, server, client, **arguments):
        instance = arguments.get("instance", None)
        dbserver = server and get_system(session, server) or None
        dbclient = client and get_system(session, client) or None
        if dbserver:
            if instance:
                return ServiceInstanceList(
                    session.query(ServiceInstance).filter_by(name=instance).join(
                    'servers').filter_by(system=dbserver).all())
            else:
                return ServiceInstanceList(
                    session.query(ServiceInstance).join('servers').filter_by(system=dbserver).all())
        elif dbclient:
            service_instances = get_client_service_instances(session, dbclient)
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return ServiceInstanceList(service_instances)
        else:
            return ServiceList(session.query(Service).all())

if __name__=='__main__':

    pass
