#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add service`."""


from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.svc.service_instance import ServiceInstance
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld
from aquilon.server.templates import (PlenaryService, PlenaryServiceInstance,
                                      PlenaryServiceInstanceClientDefault)


class CommandAddService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, comments, user, **arguments):
        dbservice = session.query(Service).filter_by(name=service).first()
        if not dbservice:
            # FIXME: Could have better error handling
            dbtld = session.query(Tld).filter_by(type="service").first()
            # Need to get or create cfgpath.
            dbcfg_path = session.query(CfgPath).filter_by(
                    tld=dbtld, relative_path=service).first()
            if not dbcfg_path:
                dbcfg_path = CfgPath(tld=dbtld, relative_path=service)
                session.save(dbcfg_path)
            dbservice = Service(name=service, cfg_path=dbcfg_path)
            session.save(dbservice)
            # Write out stub plenary data
            # By definition, we don't need to then recompile, since nothing
            # can be using this service yet.
            plenary_info = PlenaryService(dbservice)
            plenary_info.write(self.config.get("broker", "plenarydir"), user)

        if not instance:
            return

        relative_path = "%s/%s" % (service, instance)
        dbcfg_path = session.query(CfgPath).filter_by(
                tld=dbservice.cfg_path.tld, relative_path=relative_path).first()
        if not dbcfg_path:
            dbcfg_path = CfgPath(tld=dbservice.cfg_path.tld,
                    relative_path=relative_path)
            session.save(dbcfg_path)
        dbsi = ServiceInstance(service=dbservice, name=instance,
                cfg_path=dbcfg_path)
        session.save(dbsi)
        session.flush()
        session.refresh(dbservice)

        # Create the servicedata template
        plenary_info = PlenaryServiceInstance(dbservice, dbsi)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        # Create the default service template
        plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbsi)
        plenary_info.write(self.config.get("broker", "plenarydir"), user)

        return


#if __name__=='__main__':
