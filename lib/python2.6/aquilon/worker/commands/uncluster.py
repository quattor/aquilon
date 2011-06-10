# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010,2011  Contributor
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


from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.aqdb.model import Cluster
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.templates.cluster import PlenaryCluster


class CommandUncluster(BrokerCommand):

    required_parameters = ["hostname", "cluster"]

    def render(self, session, logger, hostname, cluster, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbhost = hostname_to_host(session, hostname)
        if not dbhost.cluster:
            raise ArgumentError("{0} is not bound to a cluster.".format(dbhost))
        if dbhost.cluster != dbcluster:
            raise ArgumentError("{0} is bound to {1:l}, not {2:l}.".format(
                                dbhost, dbhost.cluster, dbcluster))
        dbcluster.hosts.remove(dbhost)
        session.flush()
        session.expire(dbhost, ['_cluster'])

        # Will need to write a cluster plenary and either write or
        # remove a host plenary.  Grab the domain key since the two
        # must be in the same domain.
        host_plenary = PlenaryHost(dbhost, logger=logger)
        cluster_plenary = PlenaryCluster(dbcluster, logger=logger)
        key = CompileKey(domain=dbcluster.branch.name, logger=logger)
        try:
            lock_queue.acquire(key)
            cluster_plenary.write(locked=True)
            try:
                host_plenary.write(locked=True)
            except IncompleteError, e:
                host_plenary.cleanup(domain=dbhost.branch.name, locked=True)
        except:
            cluster_plenary.restore_stash()
            host_plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)
