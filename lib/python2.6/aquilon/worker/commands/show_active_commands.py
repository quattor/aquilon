# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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
"""Contains the logic for `aq show active commands`."""


import re
from logging import DEBUG, INFO

from aquilon.worker.broker import BrokerCommand
from aquilon.worker.messages import StatusCatalog


class CommandShowActiveCommands(BrokerCommand):

    requires_transaction = False
    requires_azcheck = False
    defer_to_thread = False

    incoming_re = re.compile(r'Incoming command #(?P<id>\d+)'
                             r' from user=(?P<user>\S+)'
                             r' aq (?P<command>\S+)'
                             r' with arguments {(?P<bareargs>.*)}')

    def render(self, debug, **arguments):
        catalog = StatusCatalog()
        retval = []
        if debug:
            loglevel = DEBUG
        else:
            # Note this is server level info!  That's more than the client
            # normally gets...
            loglevel = INFO
        # These could be streamed like show_request...
        for auditid in sorted(catalog.status_by_auditid.keys(), key=int):
            status = catalog.get_request_status(auditid=auditid)
            if not status:
                continue
            retval.append(status.description)
            for record in status.records:
                # While reading status.records directly, need to be careful
                # of any that have been removed.
                if not record:
                    continue
                if record.levelno >= loglevel:
                    message = record.getMessage()
                    if self.incoming_re.match(message):
                        # The Incoming command message is highly redundant with
                        # the status description that's already been printed.
                        continue
                    retval.append('(%s) %s' % (auditid, message))
            for description in status.subscriber_descriptions:
                retval.append(description)
        return str("\n".join(retval))
