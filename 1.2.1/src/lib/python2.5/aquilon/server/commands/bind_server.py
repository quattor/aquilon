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
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.sy.host_list import HostList
from aquilon.aqdb.sy.host_list_item import HostListItem
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
        dbhost_list = dbinstance.host_list
        session.refresh(dbhost_list)
        existing_dbhl = session.query(HostList).join('hosts').filter_by(
                host=dbhost).first()
        if existing_dbhl:
            if existing_dbhl.id == dbhost_list.id:
                # Server is already bound here, nothing to do.
                return
            if not force:
                raise ArgumentError("Host %s is already bound to %s, use unbind to clear first or rebind to force."
                        % (hostname, existing_dbhl.name))
            for dbhli in existing_dbhl.hosts:
                if dbhli.host == dbhost:
                    session.delete(dbhli)
                    session.flush()
        positions = []
        for dbhli in dbhost_list.hosts:
            positions.append(dbhli.position)
        position = 0
        while position in positions:
            position += 1
        hli = HostListItem(hostlist=dbhost_list, host=dbhost, position=position)
        session.save(hli)
        session.flush()
        session.refresh(dbhost_list)

        plenary_info = PlenaryServiceInstance(dbservice, dbinstance)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)

        # XXX: Need to recompile...

        return


#if __name__=='__main__':
