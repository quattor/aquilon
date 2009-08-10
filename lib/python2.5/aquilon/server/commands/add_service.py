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
"""Contains the logic for `aq add service`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Service, ServiceInstance, CfgPath, Tld
from aquilon.server.templates.domain import (compileLock, compileRelease)
from aquilon.server.templates.service import (PlenaryService,
                                              PlenaryServiceInstance)


class CommandAddService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, instance, comments, user, **arguments):
        dbservice = session.query(Service).filter_by(name=service).first()
        compileLock()
        #TODO: if service rows in the database exist, but the plenary files
        #are not written out, it looks like a successful add, even though
        #it will fail.
        try:
            if not dbservice:
                # FIXME: Could have better error handling
                dbtld = session.query(Tld).filter_by(type="service").first()
                # Need to get or create cfgpath.
                dbcfg_path = session.query(CfgPath).filter_by(
                    tld=dbtld, relative_path=service).first()
                if not dbcfg_path:
                    dbcfg_path = CfgPath(tld=dbtld, relative_path=service)
                    session.add(dbcfg_path)
                dbservice = Service(name=service, cfg_path=dbcfg_path)
                session.add(dbservice)

                # Note: Technically, there should be complicated logic
                # here to check that any service instance stuff that
                # follows succeeds, and only then write out this plenary
                # file (because an error there would cause a rollback).
                # However, since the service is being created new, there
                # really shouldn't be any problems below.  Taking the
                # calculated risk and just writing the service templates
                # immediately.
                session.flush()
                session.refresh(dbservice)

                # Write out stub plenary data
                # By definition, we don't need to then recompile, since nothing
                # can be using this service yet.
                plenary_info = PlenaryService(dbservice)
                plenary_info.write(locked=True)

            if not instance:
                return

            if ServiceInstance.get_unique(session, service_id=dbservice.id,
                                          name=instance):
                raise ArgumentError("Service %s instance %s already exists." %
                                    (dbservice.name, instance))

            relative_path = "%s/%s" % (service, instance)
            dbcfg_path = session.query(CfgPath).filter_by(
                tld=dbservice.cfg_path.tld, relative_path=relative_path).first()
            if not dbcfg_path:
                dbcfg_path = CfgPath(tld=dbservice.cfg_path.tld,
                                     relative_path=relative_path)
                session.add(dbcfg_path)
            dbsi = ServiceInstance(service=dbservice, name=instance,
                    cfg_path=dbcfg_path)
            session.add(dbsi)
            session.flush()
            session.refresh(dbservice)
            session.refresh(dbsi)

            # Create the servicedata template
            plenary_info = PlenaryServiceInstance(dbservice, dbsi)
            plenary_info.write(locked=True)

        finally:
            compileRelease()

        return
