# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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
"""Contains the logic for `aq compile`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.aqdb.model import Cluster, MetaCluster


def add_cluster_data(dbclus):
    def add_member_hosts(c, profile_list):
        for h in c.hosts:
            profile_list.append(h.fqdn)

    profile_list = ["clusters/%s" % dbclus.name]

    if isinstance(dbclus, MetaCluster):
        for c in dbclus.members:
            profile_list.append("clusters/%s" % c.name)
            add_member_hosts(c, profile_list)
    else:
        add_member_hosts(dbclus, profile_list)

    return profile_list


class CommandCompileCluster(BrokerCommand):

    required_parameters = ["cluster"]
    requires_readonly = True

    def render(self, session, logger, cluster,
               pancinclude, pancexclude, pancdebug, cleandeps,
               **arguments):
        dbclus = Cluster.get_unique(session, cluster, compel=True)
        if pancdebug:
            pancinclude = r'.*'
            pancexclude = r'components/spma/functions'
        dom = TemplateDomain(dbclus.branch, dbclus.sandbox_author,
                             logger=logger)
        profile_list = add_cluster_data(dbclus)

        dom.compile(session, only=profile_list,
                    panc_debug_include=pancinclude,
                    panc_debug_exclude=pancexclude,
                    cleandeps=cleandeps)
        return
