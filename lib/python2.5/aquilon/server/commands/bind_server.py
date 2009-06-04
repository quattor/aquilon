# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Contains the logic for `aq bind server`."""


from twisted.python import log

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ServiceInstanceServer
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.server.templates.service import PlenaryServiceInstance


class CommandBindServer(BrokerCommand):

    required_parameters = ["hostname", "service", "instance"]

    def render(self, session, hostname, service, instance, user, force=False, 
            **arguments):
        dbsystem = get_system(session, hostname)
        dbservice = get_service(session, service)
        dbinstance = get_service_instance(session, dbservice, instance)
        session.refresh(dbinstance)
        for dbserver in dbinstance.servers:
            if dbserver.system.id == dbsystem.id:
                # FIXME: This should just be a warning.  There is currently
                # no way of returning output that would "do the right thing"
                # on the client but still show status 200 (OK).
                # The right thing would generally be writing to stderr for
                # a CLI (either raw or csv), and some sort of generic error
                # page for a web client.
                raise ArgumentError("Server %s is already bound to service %s instance %s" %
                                    (hostname, service, instance))
        positions = []
        for dbserver in dbinstance.servers:
            positions.append(dbserver.position)
        position = 0
        while position in positions:
            position += 1
        sis = ServiceInstanceServer(service_instance=dbinstance,
                                    system=dbsystem, position=position)
        session.add(sis)
        session.flush()
        session.refresh(dbinstance)

        plenary_info = PlenaryServiceInstance(dbservice, dbinstance)
        plenary_info.write()

        # XXX: Need to recompile...

        return


