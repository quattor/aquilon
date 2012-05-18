# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq unbind client`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import (hostname_to_host,
                                            get_host_bound_service)
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.service import PlenaryServiceInstanceServer
from aquilon.worker.templates.host import PlenaryHost
from aquilon.aqdb.model import Service


class CommandUnbindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, logger, hostname, service, **arguments):
        dbhost = hostname_to_host(session, hostname)
        for srv in (dbhost.archetype.services + dbhost.personality.services):
            if srv.name == service:
                raise ArgumentError("Cannot unbind a required service. "
                                    "Perhaps you want to rebind?")

        dbservice = Service.get_unique(session, service, compel=True)
        si = get_host_bound_service(dbhost, dbservice)
        if si:
            logger.info("Removing client binding")
            dbhost.services_used.remove(si)
            session.flush()

            plenaries = PlenaryCollection(logger=logger)
            plenaries.append(PlenaryHost(dbhost, logger=logger))
            plenaries.append(PlenaryServiceInstanceServer(si, logger=logger))
            plenaries.write()

        return
