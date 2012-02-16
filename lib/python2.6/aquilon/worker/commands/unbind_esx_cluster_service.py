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


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.aqdb.model import EsxCluster, ClusterServiceBinding, Service
from aquilon.worker.dbwrappers.service_instance import get_service_instance
from aquilon.worker.templates.cluster import PlenaryCluster


class CommandUnbindESXClusterService(BrokerCommand):

    required_parameters = ["cluster", "service", "instance"]

    def render(self, session, logger, cluster, service, instance, **arguments):
        dbservice = Service.get_unique(session, service, compel=True)
        dbinstance = get_service_instance(session, dbservice, instance)
        dbcluster = EsxCluster.get_unique(session, cluster, compel=True)
        dbcsb = ClusterServiceBinding.get_unique(session, cluster=dbcluster,
                                                 service_instance=dbinstance,
                                                 compel=True)
        if dbservice in [cas.service for cas in dbcluster.required_services]:
            raise ArgumentError("Cannot remove cluster service instance "
                                "binding for %s cluster aligned service %s." %
                                (dbcluster.cluster_type, dbservice.name))
        session.delete(dbcsb)

        session.flush()

        plenary = PlenaryCluster(dbcluster, logger=logger)
        plenary.write()
        return
