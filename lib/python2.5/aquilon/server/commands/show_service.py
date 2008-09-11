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
from aquilon.server.formats.service_instance import ServiceInstanceList
from aquilon.server.dbwrappers.system import get_system

class CommandShowService(BrokerCommand):

    @add_transaction
    @az_check
    @format_results
    def render(self, session, instance, server, **arguments):
        if not instance and not server:
            return session.query(Service).all()
        q = session.query(ServiceInstance)
        if instance:
            q = q.filter_by(name=instance)
        if server:
            dbsystem = get_system(session, server)
            q = q.join('servers').filter_by(system=dbsystem)
        return ServiceInstanceList(q.all())


#if __name__=='__main__':
