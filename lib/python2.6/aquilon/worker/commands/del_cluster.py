# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.


import os

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Cluster
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.index import build_index
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.processes import remove_file
from aquilon.worker.locks import CompileKey


def del_cluster(session, logger, dbcluster, config):
    cluster = str(dbcluster.name)

    if hasattr(dbcluster, 'members') and dbcluster.members:
        raise ArgumentError("%s is still in use by clusters: %s." %
                            (format(dbcluster),
                             ", ".join([c.name for c in dbcluster.members])))
    elif dbcluster.hosts:
        hosts = ", ".join([h.fqdn for h in  dbcluster.hosts])
        raise ArgumentError("%s is still in use by hosts: %s." %
                            (format(dbcluster), hosts))
    cluster_plenary = Plenary.get_plenary(dbcluster, logger=logger)
    resources = PlenaryCollection(logger=logger)
    if dbcluster.resholder:
        for res in dbcluster.resholder.resources:
            resources.append(Plenary.get_plenary(res))
    domain = dbcluster.branch.name
    session.delete(dbcluster)

    session.flush()

    key = cluster_plenary.get_remove_key()
    with CompileKey.merge([key, resources.get_remove_key()]):
        cluster_plenary.cleanup(domain, locked=True)
        # And we also want to remove the profile itself
        profiles = config.get("broker", "profilesdir")
        # Only one of these should exist, but it doesn't hurt
        # to try to clean up both.
        xmlfile = os.path.join(profiles, "clusters", cluster + ".xml")
        remove_file(xmlfile, logger=logger)
        xmlgzfile = xmlfile + ".gz"
        remove_file(xmlgzfile, logger=logger)
        # And the cached template created by ant
        remove_file(os.path.join(config.get("broker",
                                                 "quattordir"),
                                 "objects", "clusters",
                                 cluster + ".tpl"),
                    logger=logger)
        resources.remove(locked=True)

    build_index(config, session, profiles, logger=logger)

    return


class CommandDelCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, **arguments):
        dbcluster = Cluster.get_unique(session, cluster, compel=True)
        del_cluster(session, logger, dbcluster, self.config)
