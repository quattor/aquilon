# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq bind client`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import IncompleteError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.services import Chooser
from aquilon.server.templates.host import PlenaryHost

class CommandBindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, hostname, service, instance, debug, force=False,
               **arguments):
        dbhost = hostname_to_host(session, hostname)
        dbservice = get_service(session, service)
        chooser = Chooser(dbhost, required_only=False, debug=debug)
        if instance:
            dbinstance = get_service_instance(session, dbservice, instance)
            chooser.set_single(dbservice, dbinstance, force=force)
        else:
            chooser.set_single(dbservice, force=force)

        # FIXME: Get a single compileLock for here and below.
        chooser.flush_changes()
        chooser.write_plenary_templates(locked=False)

        try:
            plenary_host = PlenaryHost(dbhost)
            plenary_host.write()
        except IncompleteError, e:
            # host has insufficient information to make a template with
            pass

        if chooser.debug_info:
            # The output of bind client does not run through a formatter.
            # Maybe it should.
            return str("\n".join(chooser.debug_info))
        return str("\n".join(chooser.messages))


