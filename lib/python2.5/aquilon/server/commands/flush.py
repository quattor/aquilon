# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq flush`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.svc.service import Service
from aquilon.aqdb.hw.machine import Machine
from aquilon.aqdb.sy.domain import Domain
from twisted.python import log
from aquilon.server.templates.service import (PlenaryService, PlenaryServiceInstance)
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.domain import compileLock, compileRelease
from aquilon.exceptions_ import PartialError, IncompleteError


class CommandFlush(BrokerCommand):

    def render(self, session, user, **arguments):
        plenarydir = self.config.get("broker", "plenarydir")
        success = []
        failed = []
        total = 0

        try:
            compileLock()

            log.msg("flushing services")
            for dbservice in session.query(Service).all():
                try:
                    total += 1
                    plenary_info = PlenaryService(dbservice)
                    plenary_info.write(plenarydir, user, locked=True)
                except Exception, e:
                    failed.append("sevice %s failed: %s" % (dbservice.name, e))
                    continue

                for dbinst in dbservice.instances:
                    try:
                        total += 1
                        plenary_info = PlenaryServiceInstance(dbservice, dbinst)
                        plenary_info.write(plenarydir, user, locked=True)
                    except Exception, e:
                        failed.append("service %s instance %s failed: %s" % (dbservice.name, dbinst.name, e))
                        continue

            log.msg("flushing machines")
            for machine in session.query(Machine).all():
                try:
                    total += 1
                    plenary_info = PlenaryMachineInfo(machine)
                    plenary_info.write(plenarydir, user, locked=True)
                except Exception, e:
                    failed.append("machine %s failed: %s" % (machine.host.fqdn, e))
                    continue

            # what about the plenary hosts within domains... do we want those too?
            # let's say yes for now...
            for d in session.query(Domain).all():
                domdir = self.config.get("broker", "builddir") + "/domains/%s/profiles"%d.name
                
                for h in d.hosts:
                    try:
                        total += 1
                        plenary_host = PlenaryHost(h)
                        plenary_host.write(domdir, user, locked=True)
                    except IncompleteError, e:
                        pass
                        #log.msg("Not flushing host: %s" % e)
                    except Exception, e:
                        failed.append("host %s in domain %s failed: %s" %(h.fqdn,d.name,e))

            log.msg("flushed %d/%d templates" % (total-len(failed), total))
            if failed:
                raise PartialError(success, failed)

        finally:
            compileRelease()

        return


