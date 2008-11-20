#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq unbind client`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_build_item)
from aquilon.server.dbwrappers.service import get_service


class CommandUnbindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, hostname, service, **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = get_service(session, service)
        dbtemplate = get_host_build_item(session, dbhost, dbservice)
        if dbtemplate:
            session.delete(dbtemplate)
            session.flush()
        session.refresh(dbhost)
        return


#if __name__=='__main__':
