#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del service`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.service import get_service
from aquilon.aqdb.service import Service, ServiceInstance, HostList
from aquilon.aqdb.configuration import CfgPath, CfgTLD


class CommandDelService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, **arguments):
        # This should fail nicely if the service is required for an archetype.
        dbservice = get_service(session, service)
        if not instance:
            if dbservice.instances:
                raise ArgumentError("Cannot remove service with instances defined.")
            session.delete(dbservice)
            return
        try:
            dbhl = session.query(HostList).filter_by(name=instance).one()
        except InvalidRequestError, e:
            raise NotFoundException(
                    "Could not find instance %s: %s"
                    % (instance, e))
        dbsi = session.query(ServiceInstance).filter_by(
                host_list=dbhl, service=dbservice).first()
        # FIXME: There may be dependencies...
        if dbsi:
            session.delete(dbsi)
        # FIXME: Cascade to relevant objects...
        return


#if __name__=='__main__':
