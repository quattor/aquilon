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


from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.branch import get_branch_and_author
from aquilon.aqdb.model import Cluster
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.base import PlenaryCollection
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.exceptions_ import IncompleteError, NotFoundException


class CommandManageCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, domain, sandbox, cluster, **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)
        dbcluster = Cluster.get_unique(session, cluster, compel=True)

        old_branch = dbcluster.branch.name
        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(PlenaryCluster(dbcluster, logger=logger))
        dbcluster.branch = dbbranch
        dbcluster.sandbox_author = dbauthor
        session.add(dbcluster)
        for dbhost in dbcluster.hosts:
            plenaries.append(PlenaryHost(dbhost, logger=logger))
            dbhost.branch = dbbranch
            dbhost.sandbox_author = dbauthor
            session.add(dbhost)

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
