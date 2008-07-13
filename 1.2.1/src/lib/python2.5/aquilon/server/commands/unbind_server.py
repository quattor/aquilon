#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq unbind server`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.sy.host_list import HostList
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandUnbindServer(BrokerCommand):

    required_parameters = ["hostname", "service"]

    @add_transaction
    @az_check
    def render(self, session, hostname, service, instance, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = get_service(session, service)
        if instance:
            dbinstance = get_service_instance(session, dbservice, instance)
        else:
            try:
                dbinstance = session.query(ServiceInstance).filter_by(
                        service=dbservice).join(
                        ["host_list", "hosts"]).filter_by(host=dbhost).one()
            except InvalidRequestError, e:
                raise ArgumentError("Could not identify a service instance to remove this host from: %s" % e)
        dbhost_list = dbinstance.host_list
        session.refresh(dbhost_list)
        for item in dbhost_list.hosts:
            if item.host == dbhost:
                session.delete(item)
        session.flush()
        session.refresh(dbhost_list)
        return


#if __name__=='__main__':
