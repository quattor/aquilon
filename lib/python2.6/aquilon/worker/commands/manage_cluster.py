# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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


from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue, CompileKey


class CommandManageCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, domain, sandbox, cluster, **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing clusters to {0:l} is not allowed."
                                .format(dbbranch))

        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        if dbcluster.metacluster:
            raise ArgumentError("{0.name} is member of metacluster {1.name}, "
                                "it must be managed at metacluster level.".
                                format(dbcluster, dbcluster.metacluster))

        old_branch = dbcluster.branch.name
        plenaries = PlenaryCollection(logger=logger)

        # manage at metacluster level
        if dbcluster.cluster_type == 'meta':
            clusters = dbcluster.members

            dbcluster.branch = dbbranch
            dbcluster.sandbox_author = dbauthor
            session.add(dbcluster)
            plenaries.append(Plenary.get_plenary(dbcluster))
        else:
            clusters = [dbcluster]

        for cluster in clusters:
            # manage at cluster level
            # Need to set the new branch *before* creating the plenary objects.
            cluster.branch = dbbranch
            cluster.sandbox_author = dbauthor
            session.add(cluster)
            plenaries.append(Plenary.get_plenary(cluster))
            for dbhost in cluster.hosts:
                dbhost.branch = dbbranch
                dbhost.sandbox_author = dbauthor
                session.add(dbhost)
                plenaries.append(Plenary.get_plenary(dbhost))

        session.flush()

        # We're crossing domains, need to lock everything.
        key = CompileKey(logger=logger)
        try:
            lock_queue.acquire(key)
            plenaries.stash()
            plenaries.cleanup(old_branch, locked=True)
            plenaries.write(locked=True)
        except:
            plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
