#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show service --service`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service_instance import get_service_instance, get_client_service_instances
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.server.formats.service_instance import ServiceInstanceList


class CommandShowServiceService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, server, client, **arguments):
        instance = arguments.get("instance", None)
        dbserver = server and get_system(session, server) or None
        dbclient = client and get_system(session, server) or None
        dbservice = get_service(session, service)
        if dbserver:
            return ServiceInstanceList(
                session.query(ServiceInstance).filter_by(service=dbservice).join(
                'servers').filter_by(system=dbserver).all())
        elif dbclient:
            service_instances = get_client_service_instances(session, dbclient)
            service_instances = [si for si in service_instances if si.service == dbservice]
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return ServiceInstanceList(service_instances)
            
        if not instance:
            return dbservice
        return get_service_instance(session, dbservice, instance)


#if __name__=='__main__':
