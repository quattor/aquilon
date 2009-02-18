# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add service`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld
from aquilon.server.templates.domain import (compileLock, compileRelease)
from aquilon.server.templates.service import (PlenaryService,
                                              PlenaryServiceInstance,
                                              PlenaryServiceClientDefault,
                                              PlenaryServiceServerDefault,
                                              PlenaryServiceInstanceServer,
                                              PlenaryServiceInstanceClientDefault,
                                              PlenaryServiceInstanceServerDefault)


class CommandAddService(BrokerCommand):

    required_parameters = ["service"]

    def render(self, session, service, instance, comments, user, **arguments):
        dbservice = session.query(Service).filter_by(name=service).first()
        compileLock();
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

                # Create the default service client and server template
                plenary_info = PlenaryServiceClientDefault(dbservice)
                plenary_info.write(locked=True)
                plenary_info = PlenaryServiceServerDefault(dbservice)
                plenary_info.write(locked=True)

            if not instance:
                return

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
            plenary_info = PlenaryServiceInstanceServer(dbservice, dbsi)
            plenary_info.write(locked=True)
            
            # Create the default service client and server template
            plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbsi)
            plenary_info.write(locked=True)
            plenary_info = PlenaryServiceInstanceServerDefault(dbservice, dbsi)
            plenary_info.write(locked=True)

        finally:
            compileRelease()
            
        return


