# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009,2010  Contributor
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


import os

from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.aqdb.model import EsxCluster
from aquilon.server.broker import BrokerCommand
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.processes import remove_file


class CommandDelESXCluster(BrokerCommand):

    required_parameters = [ "cluster" ]

    def render(self, session, logger, cluster, **arguments):
        dbcluster = EsxCluster.get_unique(session, cluster, compel=True)
        cluster = str(dbcluster.name)
        if dbcluster.machines:
            raise ArgumentError("ESX Cluster %s is still in use by virtual "
                                "machines: %s." %
                                (cluster, ", ".join([m.name for m in
                                                     dbcluster.machines])))
        if dbcluster.hosts:
            raise ArgumentError("ESX Cluster %s is still in use by vmhosts: "
                                "%s." %
                                (cluster, ", ".join([h.fqdn for h in
                                                     dbcluster.hosts])))
        dbmetacluster = dbcluster.metacluster
        plenary = PlenaryCluster(dbcluster, logger=logger)
        domain = dbcluster.branch.name
        session.delete(dbcluster)

        session.flush()

        # Cleanup the domain-specific files.
        plenary.cleanup(domain)

        # Remove the compiled profile.
        # The file is either gzip'd or not, but it doesn't hurt to try both.
        xmlfile = os.path.join(self.config.get("broker", "profilesdir"),
                               "clusters", cluster + ".xml")
        remove_file(xmlfile, logger=logger)
        xmlgzfile = xmlfile + ".gz"
        remove_file(xmlgzfile, logger=logger)
        # Remove the cache in the global profiles directory created by
        # the ant task.
        remove_file(os.path.join(self.config.get("broker", "quattordir"),
                                 "objects", "clusters", cluster + ".tpl"),
                    logger=logger)

        return
