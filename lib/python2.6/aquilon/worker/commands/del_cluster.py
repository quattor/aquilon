# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2011  Contributor
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

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.index import build_index
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.worker.processes import remove_file
from aquilon.worker.locks import lock_queue


class CommandDelCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        cluster = str(dbcluster.name)
        if dbcluster.hosts:
            hosts = ", ".join([h.fqdn for h in  dbcluster.hosts])
            raise ArgumentError("%s is still in use by hosts: %s." %
                                (format(dbcluster), hosts))
        plenary = PlenaryCluster(dbcluster, logger=logger)
        domain = dbcluster.branch.name
        session.delete(dbcluster)

        session.flush()

        key = plenary.get_remove_key()
        try:
            lock_queue.acquire(key)
            plenary.cleanup(domain, locked=True)
            # And we also want to remove the profile itself
            profiles = self.config.get("broker", "profilesdir")
            # Only one of these should exist, but it doesn't hurt
            # to try to clean up both.
            xmlfile = os.path.join(profiles, "clusters", cluster + ".xml")
            remove_file(xmlfile, logger=logger)
            xmlgzfile = xmlfile + ".gz"
            remove_file(xmlgzfile, logger=logger)
            # And the cached template created by ant
            remove_file(os.path.join(self.config.get("broker",
                                                     "quattordir"),
                                     "objects", "clusters",
                                     cluster + ".tpl"),
                        logger=logger)
            plenary.remove(locked=True)
        finally:
            lock_queue.release(key)

        build_index(self.config, session, profiles, logger=logger)

        return
