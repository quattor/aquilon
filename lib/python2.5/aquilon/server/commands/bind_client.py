# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq bind client`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.sy.build_item import BuildItem
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_build_item)
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import (get_service_instance,
                                                        choose_service_instance)

from aquilon.server.templates.service import PlenaryServiceInstanceServer

class CommandBindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, hostname, service, instance, force=False,
            **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = get_service(session, service)
        if instance:
            dbinstance = get_service_instance(session, dbservice, instance)
        else:
            dbinstance = choose_service_instance(session, dbhost, dbservice)
        dbtemplate = get_host_build_item(session, dbhost, dbservice)
        if dbtemplate:
            if dbtemplate.cfg_path == dbinstance.cfg_path:
                # Already set - no problems.
                return
            if not force:
                raise ArgumentError("Host %s is already bound to %s, use unbind to clear first or rebind to force."
                        % (hostname, dbtemplate.cfg_path.relative_path))
            session.delete(dbtemplate)
        # FIXME: Should enforce that the instance has a server bound to it.
        positions = []
        session.flush()
        session.refresh(dbhost)
        for template in dbhost.templates:
            positions.append(template.position)
            if template.cfg_path == dbinstance:
                return
        # Do not bind to 0 (os) or 1 (personality)
        i = 2
        while i in positions:
            i += 1
        bi = BuildItem(host=dbhost, cfg_path=dbinstance.cfg_path, position=i)
        session.add(bi)
        session.flush()
        session.refresh(dbhost)

        plenarydir = self.config.get("broker", "plenarydir")
        plenary_info = PlenaryServiceInstanceServer(dbservice, dbinstance)
        plenary_info.write(plenarydir)

        return


