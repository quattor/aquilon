# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq unbind client`."""


from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_build_item)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.templates.host import PlenaryHost


class CommandUnbindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, hostname, service, **arguments):
        dbhost = hostname_to_host(session, hostname)
        for item in dbhost.archetype.service_list:
            if item.service.name == service:
                raise ArgumentError("cannot unbind a required service. Perhaps you want to rebind?")
            
        dbservice = get_service(session, service)
        dbtemplate = get_host_build_item(session, dbhost, dbservice)
        if dbtemplate:
            session.delete(dbtemplate)
            session.flush()

            try:
                plenary_info = PlenaryHost(dbhost)
                plenary_info.write()
            except IncompleteError, e:
                # This template cannot be written, we leave it alone
                # It would be nice to flag the state in the the host?
                pass

            plenary_info = PlenaryServiceInstanceServer(dbservice, dbtemplate.cfg_path.svc_inst)
            plenary_info.write()

        session.refresh(dbhost)
        return


