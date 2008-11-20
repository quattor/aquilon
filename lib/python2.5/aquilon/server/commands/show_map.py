#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show map`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.service_map import ServiceMap
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.formats.service_map import ServiceMapList


class CommandShowMap(BrokerCommand):

    required_parameters = []

    def render(self, session, service, instance, **arguments):
        dbservice = service and get_service(session, service) or None
        dblocation = get_location(session, **arguments)
        # Nothing fancy for now - just show any relevant explicit bindings.
        q = session.query(ServiceMap)
        if dbservice:
            q = q.join('service_instance').filter_by(service=dbservice)
            q = q.reset_joinpoint()
        if instance:
            q = q.join('service_instance').filter_by(name=instance)
            q = q.reset_joinpoint()
        if dblocation:
            q = q.filter_by(location=dblocation)
        return ServiceMapList(q.all())


#if __name__=='__main__':
