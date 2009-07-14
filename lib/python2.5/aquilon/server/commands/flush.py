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
"""Contains the logic for `aq flush`."""


from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import (Service, Machine, Domain, Personality,
                                Cluster, MetaCluster)
from twisted.python import log
from aquilon.server.templates.personality import PlenaryPersonality
from aquilon.server.templates.cluster import (refresh_cluster_plenaries,
                                              refresh_metacluster_plenaries)
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

            log.msg("flushing personalities")
            for persona in session.query(Personality).all():
                try:
                    plenary_info = PlenaryPersonality(persona)
                    plenary_info.write(locked=True)
                    total += 1
                except Exception, e:
                    failed.append("personality %s failed: %s" %
                                  (persona.name, e))
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

            for clus in session.query(Cluster).all():
                try:
                    total += refresh_cluster_plenaries(clus, locked=True)
                except Exception, e:
                    failed.append("%s cluster %s failed: %s" %
                                  (clus.cluster_type, clus.name, e))

            for clus in session.query(MetaCluster).all():
                try:
                    total += refresh_metacluster_plenaries(clus, locked=True)
                except Exception, e:
                    failed.append("metacluster %s failed: %s" % (clus.name, e))

            log.msg("flushed %d/%d templates" % (total-len(failed), total))
            if failed:
                raise PartialError(success, failed)

        finally:
            compileRelease()

        return
