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
"""Contains a wrapper for `aq reconfigure`."""


from aquilon.server.broker import BrokerCommand
from aquilon.server.commands.make import CommandMake
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.status import get_status
from aquilon.aqdb.model import BuildItem, Archetype, Personality
from aquilon.aqdb.model.status import host_status_transitions as graph
from aquilon.exceptions_ import ArgumentError


class CommandReconfigure(CommandMake):
    """The make command mostly contains the logic required."""

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, archetype, personality, buildstatus,
               osname, osversion, os, **arguments):
        """There is some duplication here with make.

        It seemed to be the cleanest way to allow hosts with non-compileable
        archetypes to use reconfigure for buildstatus and personality.

        """
        dbhost = hostname_to_host(session, hostname)

        dbarchetype = dbhost.archetype
        if archetype and archetype != dbhost.archetype.name:
            if not personality:
                raise ArgumentError("Changing archetype also requires "
                                    "specifying --personality.")
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            # TODO: Once OS is a first class object this block needs
            # to check that either OS is also being reset or that the
            # OS is valid for the new archetype.

        # Deal with non-compileable archetypes here, leave the rest for 'make'
        if not dbarchetype.is_compileable:
            if not (buildstatus or personality or osname or osversion or os):
                raise ArgumentError("Nothing to do.")

            if buildstatus and dbhost.status.name != buildstatus:
                dbstatus = get_status(session, buildstatus)
                if buildstatus == "ready" and dbhost.cluster:
                    if dbhost.cluster.status.name != "ready":
                        logger.info("cluster is not ready, so forcing ready state to almostready")
                        buildstatus = "almostready"

                if buildstatus not in graph:
                    raise ArgumentError("state '%s' is not valid. Try one of: %s" %
                                        (buildstatus, ", ".join(graph.keys())))

                if buildstatus not in graph[dbhost.status.name]:
                    raise ArgumentError("cannot change state to '%s' from '%s'. Legal states are: %s" %
                                        (buildstatus, dbhost.status.name,
                                         ", ".join(graph[dbhost.status.name])))
                dbhost.status = dbstatus


            if personality:
                dbpersonality = Personality.get_unique(session,
                                                       name=personality,
                                                       archetype=dbarchetype,
                                                       compel=True)
                # This check was written blind... as of this being added
                # we don't have any non-compilable archetypes that can be
                # a part of a cluster.
                if dbhost.cluster and \
                   dbhost.cluster.personality != dbpersonality:
                    raise ArgumentError("Cannot change personality of host %s "
                                        "while it is a member of "
                                        "%s cluster %s." %
                                        (dbhost.fqdn,
                                         dbhost.cluster.cluster_type,
                                         dbhost.cluster.name))
                dbhost.personality = dbpersonality
            if osname or osversion or os:
                dbos = self.get_os(session, dbhost, osname, osversion, os)
                if dbos:
                    dbhost.operating_system = dbos
            session.add(dbhost)
            return

        return CommandMake.render(self, session=session, logger=logger, hostname=hostname,
                                  archetype=archetype, personality=personality,
                                  osname=osname, osversion=osversion, os=os,
                                  buildstatus=buildstatus, **arguments)


