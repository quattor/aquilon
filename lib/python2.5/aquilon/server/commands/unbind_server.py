# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq unbind server`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.svc.service_instance_server import ServiceInstanceServer
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance

from aquilon.server.templates.service import PlenaryServiceInstance


class CommandUnbindServer(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, hostname, service, instance, user, **arguments):
        dbsystem = get_system(session, hostname)
        dbservice = get_service(session, service)
        if instance:
            dbinstances = [get_service_instance(session, dbservice, instance)]
        else:
            dbinstances = session.query(ServiceInstance).filter_by(
                    service=dbservice).filter(
                        ServiceInstance.id==
                            ServiceInstanceServer.service_instance_id
                    ).filter(ServiceInstanceServer.system==dbsystem).all()
        for dbinstance in dbinstances:
            for item in dbinstance.servers:
                if item.system == dbsystem:
                    session.delete(item)
        session.flush()
        for dbinstance in dbinstances:
            session.refresh(dbinstance)
            plenary_info = PlenaryServiceInstance(dbservice, dbinstance)
            plenary_info.write()

        # XXX: Need to recompile...
        return


