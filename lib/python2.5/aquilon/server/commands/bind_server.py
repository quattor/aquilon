# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq bind server`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.svc.service_instance_server import ServiceInstanceServer
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.templates.service import PlenaryServiceInstance


class CommandBindServer(BrokerCommand):

    required_parameters = ["hostname", "service", "instance"]

    @add_transaction
    @az_check
    def render(self, session, hostname, service, instance, user, force=False, 
            **arguments):
        dbsystem = get_system(session, hostname)
        dbservice = get_service(session, service)
        dbinstance = get_service_instance(session, dbservice, instance)
        session.refresh(dbinstance)
        for dbserver in dbinstance.servers:
            if dbserver.system.id == dbsystem.id:
                # FIXME: This should just be a warning.  There is currently
                # no way of returning output that would "do the right thing"
                # on the client but still show status 200 (OK).
                # The right thing would generally be writing to stderr for
                # a CLI (either raw or csv), and some sort of generic error
                # page for a web client.
                raise ArgumentError("Server %s is already bound to service %s instance %s" %
                                    (hostname, service, instance))
        positions = []
        for dbserver in dbinstance.servers:
            positions.append(dbserver.position)
        position = 0
        while position in positions:
            position += 1
        sis = ServiceInstanceServer(service_instance=dbinstance,
                                    system=dbsystem, position=position)
        session.save(sis)
        session.flush()
        session.refresh(dbinstance)

        plenary_info = PlenaryServiceInstance(dbservice, dbinstance)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        # XXX: Need to recompile...

        return


