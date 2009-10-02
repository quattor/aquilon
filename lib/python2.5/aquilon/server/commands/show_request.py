# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2009 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq show request`."""


from time import sleep
from logging import DEBUG

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.logger import CLIENT_INFO


class CommandShowRequest(BrokerCommand):

    def render(self, requestid, request, logger, debug, **arguments):
        status = logger.get_status()
        if not status:
            raise NotFoundException("requestid %s not found" % requestid)
        reported = 0
        if debug:
            loglevel = DEBUG
        else:
            loglevel = CLIENT_INFO
        while request.channel.transport.connected:
            current = status.get_new(reported)
            if current != reported:
                messages = [record.getMessage() for record
                            in status.records[reported:current]
                            if record.levelno >= loglevel]
                request.write(str("\n".join(messages)))
                reported = current
            if status.is_finished and reported == len(status.records):
                break
        return ''


