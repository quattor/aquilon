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
"""Contains the logic for `aq show service --service`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.dbwrappers.service_instance import get_service_instance, get_client_service_instances
from aquilon.aqdb.model import ServiceInstance
from aquilon.server.formats.service_instance import ServiceInstanceList


class CommandShowServiceService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, server, client, **arguments):
        instance = arguments.get("instance", None)
        dbserver = server and get_system(session, server) or None
        dbclient = client and get_system(session, client) or None
        dbservice = get_service(session, service)
        if dbserver:
            return ServiceInstanceList(
                session.query(ServiceInstance).filter_by(service=dbservice).join(
                'servers').filter_by(system=dbserver).all())
        elif dbclient:
            service_instances = get_client_service_instances(session, dbclient)
            service_instances = [si for si in service_instances if si.service == dbservice]
            if instance:
                service_instances = [si for si in service_instances if si.name == instance]
            return ServiceInstanceList(service_instances)
            
        if not instance:
            return dbservice
        return get_service_instance(session, dbservice, instance)


