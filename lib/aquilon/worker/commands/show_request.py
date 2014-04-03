# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq show request`."""


from logging import DEBUG

from twisted.internet.defer import Deferred

from aquilon.exceptions_ import NotFoundException
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.logger import CLIENT_INFO
from aquilon.worker.messages import StatusSubscriber


class StatusWriter(StatusSubscriber):
    def __init__(self, deferred, request, loglevel):
        StatusSubscriber.__init__(self)
        self.deferred = deferred
        self.request = request
        self.loglevel = loglevel

    def process(self, record):
        # TODO: As documented in the twisted http module, should
        # instead register a notifyFinish callback to track clients
        # disconnecting.
        if self.request._disconnected:
            return
        if record.levelno >= self.loglevel:
            msg = record.getMessage() or ''
            if msg:
                msg = "%s\n" % msg
            self.request.write(str(msg))

    def finish(self):
        if not self.deferred.called:
            self.deferred.callback('')


class CommandShowRequest(BrokerCommand):

    requires_azcheck = False
    requires_transaction = False
    requires_format = False
    defer_to_thread = False

    required_parameters = ["requestid"]

    def render(self, request, debug, requestid=None, auditid=None, **arguments):
        status = self.catalog.get_request_status(auditid=auditid,
                                                 requestid=requestid)
        if not status:
            if requestid:
                raise NotFoundException("Request ID %s not found." % requestid)
            else:
                raise NotFoundException("Audit ID %s not found." % auditid)
        if debug:
            loglevel = DEBUG
        else:
            loglevel = CLIENT_INFO
        deferred = Deferred()
        status.add_subscriber(StatusWriter(deferred, request, loglevel))
        return deferred
