# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013  Contributor
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


from aquilon.worker.broker import BrokerCommand, validate_basic
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.location import get_location
from aquilon.aqdb.model import (MetaCluster, Personality, ClusterLifecycle,
                                Location)
from aquilon.worker.templates.metacluster import PlenaryMetaCluster
from aquilon.exceptions_ import ArgumentError


class CommandAddMetaCluster(BrokerCommand):

    required_parameters = ["metacluster"]

    def render(self, session, logger,
               metacluster, archetype, personality,
               domain, sandbox,
               max_members, max_shares,
               buildstatus, comments,
               **arguments):

        validate_basic("metacluster", metacluster)

        # this should be reverted when virtbuild supports these options
        if not archetype:
            archetype = "metacluster"

        if not personality:
            personality = "metacluster"

        dbpersonality = Personality.get_unique(session, name=personality,
                                               archetype=archetype, compel=True)
        if not dbpersonality.is_cluster:
            raise ArgumentError("%s is not a cluster personality." %
                                personality)

        ctype = "meta"  # dbpersonality.archetype.cluster_type

        if not buildstatus:
            buildstatus = "build"
        dbstatus = ClusterLifecycle.get_unique(session, buildstatus,
                                               compel=True)

        # this should be reverted when virtbuild supports these options
        if not domain and not sandbox:
            domain = self.config.get("broker", "metacluster_host_domain")

        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=False)

        dbloc = get_location(session, **arguments)

        # this should be reverted when virtbuild supports this option
        if not dbloc:
            dbloc = Location.get_unique(session,
                                        name=self.config.get("broker",
                                                 "metacluster_location_name"),
                                        location_type=self.config.get("broker",
                                                  "metacluster_location_type"))
        elif not dbloc.campus:
            raise ArgumentError("{0} is not within a campus.".format(dbloc))

        if max_members is None:
            max_members = self.config.getint("broker",
                                             "metacluster_max_members_default")

        if max_shares is None:
            max_shares = self.config.getint("broker",
                                            "metacluster_max_shares_default")

        if metacluster.strip().lower() == 'global':
            raise ArgumentError("Metacluster name global is reserved.")

        MetaCluster.get_unique(session, metacluster, preclude=True)
        clus_type = MetaCluster  # Cluster.__mapper__.polymorphic_map[ctype].class_

        kw = {}

        dbcluster = MetaCluster(name=metacluster, location_constraint=dbloc,
                                personality=dbpersonality,
                                max_clusters=max_members, max_shares=max_shares,
                                branch=dbbranch, sandbox_author=dbauthor,
                                status=dbstatus, comments=comments)

        session.add(dbcluster)
        session.flush()

        plenary = PlenaryMetaCluster(dbcluster, logger=logger)
        plenary.write()

        return
