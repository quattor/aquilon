#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq flush`."""


from aquilon.server.broker import (add_transaction, az_check, BrokerCommand)
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.hw.machine import Machine
from twisted.python import log
from aquilon.server.templates import (PlenaryService, PlenaryServiceInstance, PlenaryMachineInfo)


class CommandFlush(BrokerCommand):

    @add_transaction
    @az_check
    def render(self, session, user, **arguments):
        plenarydir = self.config.get("broker", "plenarydir")
        servername = self.config.get("broker", "servername")
        hostsdir = self.config.get("broker", "hostsdir")
        success = []
        failed = []
        total = 0

        log.msg("flushing services")
        # This should grab a global lock...
        for dbservice in session.query(Service).all():
            try:
                total += 1
                plenary_info = PlenaryService(dbservice)
                plenary_info.write(plenarydir, servername, user)
            except Exception, e:
                failed.append("sevice %s failed: %s" % (dbservice.name, e))
                continue
            
            for dbinst in dbservice.instances:
                try:
                    total += 1
                    plenary_info = PlenaryServiceInstance(dbservice, dbinst)
                    plenary_info.write(plenarydir, servername, user)
                except Exception, e:
                    failed.append("service %s instance %s failed: %s" % (dbservice.name, dbinst.host_list.name, e))
                    continue

        log.msg("flushing machines")
        for machine in session.query(Machine).all():
            try:
                total += 1
                plenary_info = PlenaryMachineInfo(machine)
                plenary_info.write(plenarydir, servername, user)
            except Exception, e:
                failed.append("machine %s failed: %s" % (dbmachine.host.fqdn, e))
                continue

        log.msg("flushed %d/%d templates" % (total-len(failed), total))
        if failed:
            raise PartialError(success, failed)
        return

#if __name__=='__main__':
