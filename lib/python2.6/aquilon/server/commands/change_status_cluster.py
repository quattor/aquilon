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
"""Contains the logic for `aq change status`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.status import get_status
from aquilon.server.templates.domain import TemplateDomain
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.aqdb.model import Cluster

class CommandChangeClusterStatus(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, buildstatus, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if not dbcluster.status.transition(session, dbcluster, buildstatus):
            return

        # Promote the members of the cluster
        new_promotes = []
        plenaries = []
        if dbcluster.status.name == "ready":
            for dbhost in dbcluster.hosts:
                if dbhost.status.name == 'almostready':
                    if dbhost.status.transition(session, dbhost, 'ready'):
                        logger.info("promoted %s from almostready to ready" % dbhost.fqdn)
                        new_promotes.append(dbhost.fqdn)
                        hostfile = PlenaryHost(dbhost, logger=logger)
                        plenaries.append(hostfile)
                    
        if not dbcluster.personality.archetype.is_compileable:
            return

        session.flush()

        plenary = PlenaryCluster(dbcluster, logger=logger)
        plenaries.append(plenary)
        # Force a host lock as pan might overwrite the profile...
        key = CompileKey(domain=dbcluster.branch.name, profile=dbcluster.name,
                         logger=logger)
        try:
            lock_queue.acquire(key)
            for tpl in plenaries:
                tpl.write(locked=True)
            td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                                logger=logger)
            out = td.compile(session, only=" ".join(new_promotes), locked=True)
            # We cannnot get an incomplete exception, because new_promotes are all
            # hosts that are in almostready status, therefore they must be complete.
        except:
            for tpl in plenaries:
                tpl.restore_stash()
            raise
        finally:
            lock_queue.release(key)
        return
