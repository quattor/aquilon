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
from aquilon.aqdb.sy.host_list import HostList
from aquilon.aqdb.cfg.cfg_path import CfgPath
from aquilon.aqdb.cfg.tld import Tld


class CommandAddService(BrokerCommand):

    required_parameters = ["service"]

    @add_transaction
    @az_check
    def render(self, session, service, instance, comments, **arguments):
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
        if not instance:
            return

        # FIXME: Check that assuming hostlist name is unique is correct...
        dbhostlist = session.query(HostList).filter_by(name=instance).first()
        if not dbhostlist:
            dbhostlist = HostList(name=instance)
            session.save(dbhostlist)
        # FIXME: This will autocreate a service/instance CfgPath.  Does
        # there need to be a separate/explicit create of a
        # service/instance/client CfgPath?
        # Update: See AQUILONAQD-82
        relative_path = "%s/%s" % (service, instance)
        dbcfg_path = session.query(CfgPath).filter_by(
                tld=dbservice.cfg_path.tld, relative_path=relative_path).first()
        if not dbcfg_path:
            dbcfg_path = CfgPath(tld=dbservice.cfg_path.tld,
                    relative_path=relative_path)
            session.save(dbcfg_path)
        dbsi = ServiceInstance(service=dbservice, host_list=dbhostlist,
                cfg_path=dbcfg_path)
        session.save(dbsi)
        session.flush()
        session.refresh(dbservice)
        return


#if __name__=='__main__':
