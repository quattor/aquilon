# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq flush`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Service, Machine, Domain
from twisted.python import log
from aquilon.server.templates.service import (PlenaryService, PlenaryServiceInstance,
                                              PlenaryServiceInstanceServer,
                                              PlenaryServiceClientDefault, PlenaryServiceServerDefault,
                                              PlenaryServiceInstanceClientDefault,
                                              PlenaryServiceInstanceServerDefault)
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.domain import compileLock, compileRelease
from aquilon.exceptions_ import PartialError, IncompleteError


class CommandFlush(BrokerCommand):

    def render(self, session, user, **arguments):
        success = []
        failed = []
        total = 0

        try:
            compileLock()

            log.msg("flushing services")
            for dbservice in session.query(Service).all():
                try:
                    total += 3
                    plenary_info = PlenaryService(dbservice)
                    plenary_info.write(locked=True)
                    plenary_info = PlenaryServiceClientDefault(dbservice)
                    plenary_info.write(locked=True)
                    plenary_info = PlenaryServiceServerDefault(dbservice)
                    plenary_info.write(locked=True)
                except Exception, e:
                    failed.append("service %s failed: %s" % (dbservice.name, e))
                    continue

                for dbinst in dbservice.instances:
                    try:
                        total += 4
                        plenary_info = PlenaryServiceInstance(dbservice, dbinst)
                        plenary_info.write(locked=True)
                        plenary_info = PlenaryServiceInstanceServer(dbservice, dbinst)
                        plenary_info.write(locked=True)
                        plenary_info = PlenaryServiceInstanceClientDefault(dbservice, dbinst)
                        plenary_info.write(locked=True)
                        plenary_info = PlenaryServiceInstanceServerDefault(dbservice, dbinst)
                        plenary_info.write(locked=True)
                    except Exception, e:
                        failed.append("service %s instance %s failed: %s" % (dbservice.name, dbinst.name, e))
                        continue

            log.msg("flushing machines")
            for machine in session.query(Machine).all():
                try:
                    total += 1
                    plenary_info = PlenaryMachineInfo(machine)
                    plenary_info.write(locked=True)
                except Exception, e:
                    label = machine.name
                    if machine.host:
                        label = "%s (host: %s)" % (machine.name,
                                                   machine.host.fqdn)
                    failed.append("machine %s failed: %s" % (label, e))
                    continue

            # what about the plenary hosts within domains... do we want those too?
            # let's say yes for now...
            for d in session.query(Domain).all():
                for h in d.hosts:
                    try:
                        total += 1
                        plenary_host = PlenaryHost(h)
                        plenary_host.write(locked=True)
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
