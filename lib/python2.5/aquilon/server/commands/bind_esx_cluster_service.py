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


from aquilon.exceptions_ import NotFoundException, ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import EsxCluster, ClusterAlignedService, ClusterServiceBinding
from aquilon.server.dbwrappers.service import get_service
from aquilon.server.dbwrappers.service_instance import get_service_instance


class CommandBindESXClusterService(BrokerCommand):

    required_parameters = ["cluster", "service", "instance"]

    def render(self, session, cluster, service, instance, force=False,
               **arguments):
        cluster_type = 'esx'
        dbservice = get_service(session, service)
        dbinstance = get_service_instance(session, dbservice, instance)
        dbcluster = EsxCluster.get_unique(session, cluster)
        if not dbcluster:
            raise NotFoundException("%s cluster '%s' not found." %
                                    (cluster_type, cluster))
        dbcas = ClusterAlignedService.get_unique(session,
                                                 service_id=dbservice.id,
                                                 cluster_type=cluster_type)
        if not dbcas:
            raise ArgumentError("Cannot bind a cluster to a service that "
                                "is not cluster aligned.")

        q = session.query(ClusterServiceBinding).filter_by(cluster=dbcluster)
        q = q.join('service_instance').filter_by(service=dbservice)
        dbcsb = q.first()
        if dbcsb:
            if dbcsb.service_instance == dbinstance:
                # Go ahead and rewrite the plenary.
                pass
            elif force:
                session.delete(dbcsb)
                dbcsb = None
            else:
                raise ArgumentError("Cannot bind %s cluster %s to service %s "
                                    "instance %s: cluster already bound to "
                                    "instance %s.  Use rebind to change." %
                                    (cluster_type, dbcluster.name,
                                     dbservice.name, dbinstance.name,
                                     dbcsb.service_instance.name))
        if not dbcsb:
            dbcsb = ClusterServiceBinding(cluster=dbcluster,
                                          service_instance=dbinstance)
            session.add(dbcsb)

        # XXX: This does not update the cluster members.
        dbsession.flush()

        # FIXME: Rewrite/add the appropriate plenary files
        return


