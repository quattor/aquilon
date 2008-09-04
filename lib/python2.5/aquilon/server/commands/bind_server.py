#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq bind server`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.svc.service_instance_server import ServiceInstanceServer
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_build_item)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.templates import PlenaryServiceInstance


class CommandBindServer(BrokerCommand):

    required_parameters = ["hostname", "service", "instance"]

    @add_transaction
    @az_check
    def render(self, session, hostname, service, instance, user, force=False, 
            **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = get_service(session, service)
        dbinstance = get_service_instance(session, dbservice, instance)
        session.refresh(dbinstance)
        for dbserver in dbinstance.servers:
            if dbserver.system.id == dbhost.id:
                # Server is already bound here, nothing to do.
                return
        positions = []
        for dbserver in dbinstance.servers:
            positions.append(dbserver.position)
        position = 0
        while position in positions:
            position += 1
        sis = ServiceInstanceServer(service_instance=dbinstance,
                                    system=dbhost, position=position)
        session.save(sis)
        session.flush()
        session.refresh(dbinstance)

        plenary_info = PlenaryServiceInstance(dbservice, dbinstance)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        # XXX: Need to recompile...

        return


#if __name__=='__main__':
