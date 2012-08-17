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
"""Contains the logic for `aq cat --cluster`."""


from aquilon.aqdb.model import Cluster, MetaCluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.resources import get_resource
from aquilon.worker.templates.base import Plenary
from aquilon.worker.templates.cluster import (PlenaryClusterObject,
                                              PlenaryClusterData)
from aquilon.worker.templates.metacluster import (PlenaryMetaClusterObject,
                                              PlenaryMetaClusterData)

class CommandCatCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, data, generate, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        dbresource = get_resource(session, dbcluster, **arguments)
        if dbresource:
            plenary_info = Plenary.get_plenary(dbresource, logger=logger)
        else:
            if isinstance(dbcluster, MetaCluster):
                if data:
                    plenary_info = PlenaryMetaClusterData(dbcluster, logger=logger)
                else:
                    plenary_info = PlenaryMetaClusterObject(dbcluster, logger=logger)
            else:
                if data:
                    plenary_info = PlenaryClusterData(dbcluster, logger=logger)
                else:
                    plenary_info = PlenaryClusterObject(dbcluster, logger=logger)

        if generate:
            return plenary_info._generate_content()
        else:
            return plenary_info.read()
