#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq del required service`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.service_list_item import ServiceListItem
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.server.dbwrappers.service import get_service


class CommandDelRequiredService(BrokerCommand):

    required_parameters = ["service", "archetype"]

    def render(self, session, service, archetype, **arguments):
        dbarchetype = get_archetype(session, archetype)
        dbservice = get_service(session, service)
        try:
            dbsli = session.query(ServiceListItem).filter_by(
                    service=dbservice, archetype=dbarchetype).one()
        except InvalidRequestError, e:
            raise NotFoundException("Could not find required service %s for %s: %s"
                    % (service, archetype, e))
        session.delete(dbsli)
        session.refresh(dbarchetype)
        return


#if __name__=='__main__':
