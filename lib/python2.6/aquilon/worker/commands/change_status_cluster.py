# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011,2012  Contributor
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


from aquilon.exceptions_ import IncompleteError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.aqdb.model import Cluster, ClusterLifecycle

class CommandChangeClusterStatus(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, buildstatus, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbstatus = ClusterLifecycle.get_unique(session, buildstatus,
                                                    compel=True)

        if not dbcluster.status.transition(dbcluster, dbstatus):
            return

        if not dbcluster.personality.archetype.is_compileable:
            return

        session.flush()

        plenaries = []
        plenary = PlenaryCluster(dbcluster, logger=logger)
        plenaries.append(plenary)

        # recompile all of the hosts associated with the cluster
        compilelist = []
        compilelist.append("cluster/" + dbcluster.name)
        for dbhost in dbcluster.hosts:
            hostfile = PlenaryHost(dbhost, logger=logger)
            plenaries.append(hostfile)
            compilelist.append(dbhost.fqdn)

        # Force a host lock as pan might overwrite the profile...
        key = CompileKey(domain=dbcluster.branch.name, logger=logger)
        try:
            lock_queue.acquire(key)

            for tpl in plenaries:
                try:
                    tpl.write(locked=True)
                except IncompleteError:
                    # some hosts may not be built yet
                    logger.client_info("Failed to refresh the plenary of {0:l}; "
                                       "please run 'reconfigure'."
                                       .format(tpl.dbobj))

            td = TemplateDomain(dbcluster.branch, dbcluster.sandbox_author,
                                logger=logger)
            td.compile(session, " ".join(compilelist), locked=True)

        except:
            for tpl in plenaries:
                tpl.restore_stash()
            raise
        finally:
            lock_queue.release(key)
        return
