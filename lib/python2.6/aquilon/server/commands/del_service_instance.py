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
"""Contains a wrapper for `aq del service --instance`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service_instance import get_service_instance
from aquilon.aqdb.model import Service, ServiceMap, PersonalityServiceMap
from aquilon.server.templates.service import PlenaryServiceInstance


class CommandDelServiceInstance(BrokerCommand):

    required_parameters = ["service", "instance"]

    def render(self, session, logger, service, instance, **arguments):
        dbservice = Service.get_unique(session, service, compel=True)
        dbsi = get_service_instance(session, dbservice, instance)
        if dbsi.client_count > 0:
            raise ArgumentError("Service %s, instance %s still has clients and "
                                "cannot be deleted." %
                                (dbservice.name, dbsi.name))
        if dbsi.servers:
            msg = ", ".join([item.host.fqdn for item in dbsi.servers])
            raise ArgumentError("Service %s, instance %s is still being "
                                "provided by servers: %s." %
                                (dbservice.name, dbsi.name, msg))

        # Check the service map and remove any mappings
        for dbmap in session.query(ServiceMap).filter_by(
                service_instance=dbsi).all():
            session.delete(dbmap)
        for dbmap in session.query(PersonalityServiceMap).filter_by(
                service_instance=dbsi).all():
            session.delete(dbmap)

        session.delete(dbsi)
        session.flush()

        plenary_info = PlenaryServiceInstance(dbservice, dbsi, logger=logger)
        plenary_info.remove()

        return
