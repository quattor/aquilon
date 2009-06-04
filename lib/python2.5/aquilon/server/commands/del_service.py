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
"""Contains the logic for `aq del service`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service import get_service
from aquilon.aqdb.model import (ServiceInstance, ServiceMap,
                                 PersonalityServiceMap)
from aquilon.server.templates.service import (PlenaryService,
        PlenaryServiceClientDefault, PlenaryServiceServerDefault,
        PlenaryServiceInstance, PlenaryServiceInstanceServer,
        PlenaryServiceInstanceClientDefault,
        PlenaryServiceInstanceServerDefault)


class CommandDelService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, instance, **arguments):
        # This should fail nicely if the service is required for an archetype.
        dbservice = get_service(session, service)
        if not instance:
            if dbservice.instances:
                raise ArgumentError("Cannot remove service with instances defined.")

            session.delete(dbservice)
            session.flush()

            plenary_info = PlenaryService(dbservice)
            plenary_info.remove()

            plenary_info = PlenaryServiceClientDefault(dbservice)
            plenary_info.remove()

            plenary_info = PlenaryServiceServerDefault(dbservice)
            plenary_info.remove()

            return
        dbsi = session.query(ServiceInstance).filter_by(
                name=instance, service=dbservice).first()

        if dbsi:
            if dbsi.client_count > 0:
                raise ArgumentError("instance has clients and cannot be deleted.")
            if dbsi.servers:
                raise ArgumentError("instance is still being provided by servers.")

            # Check the service map and remove any mappings
            for dbmap in session.query(ServiceMap).filter_by(
                    service_instance=dbsi).all():
                session.delete(dbmap)
            for dbmap in session.query(PersonalityServiceMap).filter_by(
                    service_instance=dbsi).all():
                session.delete(dbmap)

            session.delete(dbsi)
            session.flush()

            plenary_info = PlenaryServiceInstance(dbservice, dbsi)
            plenary_info.remove()

            plenary_info = PlenaryServiceInstanceServer(dbservice, dbsi)
            plenary_info.remove()

            plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbsi)
            plenary_info.remove()

            plenary_info = PlenaryServiceInstanceServerDefault(dbservice, dbsi)
            plenary_info.remove()

        # FIXME: Cascade to relevant objects...
        return
