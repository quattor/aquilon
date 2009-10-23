# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show request --auditid`."""


from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.show_request import CommandShowRequest


class CommandShowRequestAuditID(CommandShowRequest):

    def render(self, auditid, request, logger, **arguments):
        status = logger.get_status()
        if not status:
            raise NotFoundException("auditid %s not found" % auditid)
        arguments.pop("requestid")
        return CommandShowRequest.render(self, requestid=status.requestid,
                                         request=request, logger=logger,
                                         **arguments)


