# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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


from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.host import (hostname_to_host,
                                            get_host_build_item)
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.templates.service import PlenaryServiceInstanceServer
from aquilon.server.templates.host import PlenaryHost
from aquilon.aqdb.model import Service


class CommandUnbindClient(BrokerCommand):

    required_parameters = ["hostname", "service"]

    def render(self, session, logger, hostname, service, **arguments):
        dbhost = hostname_to_host(session, hostname)
        for item in (dbhost.archetype.service_list +
                     dbhost.personality.service_list):
            if item.service.name == service:
                raise ArgumentError("cannot unbind a required service. Perhaps you want to rebind?")

        dbservice = Service.get_unique(session, service, compel=True)
        dbtemplate = get_host_build_item(session, dbhost, dbservice)
        if dbtemplate:
            logger.info("Removing client binding")
            si = dbtemplate.service_instance
            session.delete(dbtemplate)
            session.flush()

            plenaries = PlenaryCollection(logger=logger)
            plenaries.append(PlenaryHost(dbhost, logger=logger))
            plenaries.append(PlenaryServiceInstanceServer(dbservice, si,
                                                          logger=logger))
            plenaries.write()

        return
