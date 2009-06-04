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
"""Contains the logic for `aq unmap service`."""

from aquilon.exceptions_ import UnimplementedError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import ServiceMap, PersonalityServiceMap
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandUnmapService(BrokerCommand):

    required_parameters = ["service", "instance", "archetype"]

    def render(self, session, service, instance, archetype, personality,
               **arguments):
        dbservice = get_service(session, service)
        dblocation = get_location(session, **arguments)
        dbinstance = get_service_instance(session, dbservice, instance)

        # The archetype is required, so will always be set.
        if personality:
            dbpersona = get_personality(session, archetype, personality)
            dbmap = session.query(PersonalityServiceMap).filter_by(
                personality=dbpersona)
        elif archetype != 'aquilon':
            raise UnimplementedError("Archetype level ServiceMaps other "
                                     "than aquilon are not yet available")
        else:
            dbmap = session.query(ServiceMap)

        dbmap = dbmap.filter_by(location=dblocation,
                service_instance=dbinstance).first()

        if dbmap:
            session.delete(dbmap)
        session.flush()
        session.refresh(dbservice)
        session.refresh(dbinstance)
        return
