# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the EU DataGrid Software License.  You should
# have received a copy of the license with this program, and the
# license is published at
# http://eu-datagrid.web.cern.ch/eu-datagrid/license.html.
#
# THE FOLLOWING DISCLAIMER APPLIES TO ALL SOFTWARE CODE AND OTHER
# MATERIALS CONTRIBUTED IN CONNECTION WITH THIS PROGRAM.
#
# THIS SOFTWARE IS LICENSED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE AND ANY WARRANTY OF NON-INFRINGEMENT, ARE
# DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS
# BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY,
# OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT
# OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR
# BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF
# LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING
# NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE. THIS
# SOFTWARE MAY BE REDISTRIBUTED TO OTHERS ONLY BY EFFECTIVELY USING
# THIS OR ANOTHER EQUIVALENT DISCLAIMER AS WELL AS ANY OTHER LICENSE
# TERMS THAT MAY APPLY.
"""Contains the logic for `aq show request`."""


from logging import DEBUG

from twisted.internet.defer import Deferred

from aquilon.exceptions_ import NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.logger import CLIENT_INFO
from aquilon.server.messages import StatusSubscriber


class StatusWriter(StatusSubscriber):
    def __init__(self, deferred, request, loglevel):
        StatusSubscriber.__init__(self)
        self.deferred = deferred
        self.request = request
        self.loglevel = loglevel

    def process(self, record):
        if record.levelno >= self.loglevel and \
           self.request.channel.transport.connected:
            self.request.write(str(record.getMessage()))

    def finish(self):
        if not self.deferred.called:
            self.deferred.callback('')


class CommandShowRequest(BrokerCommand):

    requires_azcheck = False
    requires_transaction = False
    requires_format = False
    defer_to_thread = False

    def render(self, requestid, request, logger, debug, **arguments):
        status = logger.get_status()
        if not status:
            raise NotFoundException("Request ID %s not found." % requestid)
        if debug:
            loglevel = DEBUG
        else:
            loglevel = CLIENT_INFO
        deferred = Deferred()
        status.add_subscriber(StatusWriter(deferred, request, loglevel))
        return deferred


