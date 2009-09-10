# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2009  Contributor
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
"""Contains the logic for `aq make`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.personality import get_personality
from aquilon.server.dbwrappers.host import hostname_to_host
from aquilon.server.dbwrappers.status import get_status
from aquilon.aqdb.model import BuildItem
from aquilon.server.templates.domain import TemplateDomain
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.services import Chooser

class CommandMake(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, hostname, os, archetype, personality,
               buildstatus, debug, **arguments):
        dbhost = hostname_to_host(session, hostname)

        # We grab a template compile lock over this whole operation,
        # which means that we will wait until any outstanding compiles
        # have completed before we start modifying files within template
        # domains.
        chooser = None
        try:
            compileLock()

            # Currently, for the Host to be created it *must* be associated with
            # a Machine already.  If that ever changes, need to check here and
            # bail if dbhost.machine does not exist.

            # Need to get all the BuildItem/Service instance objects
            if personality:
                arch = archetype
                if not arch:
                    arch = dbhost.archetype.name

                dbpersonality = get_personality(session, arch, personality)
                if dbhost.cluster and \
                   dbhost.cluster.personality != dbpersonality:
                    raise ArgumentError("Cannot change personality of host %s "
                                        "while it is a member of "
                                        "%s cluster %s" %
                                        (dbhost.fqdn,
                                         dbhost.cluster.cluster_type,
                                         dbhost.cluster.name))
                dbhost.personality = dbpersonality

            if not dbhost.archetype.is_compileable:
                raise ArgumentError("Host %s is not a compilable archetype (%s)" %
                        (hostname, dbhost.archetype.name))

            if buildstatus:
                dbstatus = get_status(session, buildstatus)
                dbhost.status = dbstatus
                session.add(dbhost)

            session.flush()

            if arguments.get("keepbindings", None):
                chooser = Chooser(dbhost, required_only=False, debug=debug)
            else:
                chooser = Chooser(dbhost, required_only=True, debug=debug)
            chooser.set_required()
            chooser.flush_changes()
            chooser.write_plenary_templates(locked=True)

            td = TemplateDomain(dbhost.domain)
            out = td.compile(session, only=dbhost.fqdn, locked=True)

        except:
            #if chooser:
                #chooser.restore_stash()

            # Okay, cleaned up templates, make sure the caller knows
            # we've aborted so that DB can be appropriately rollback'd.

            # Error will not include any debug output...
            raise

        finally:
            compileRelease()

        # If out is empty, make sure we use an empty list to prevent
        # an extra newline below.
        out_array = out and [out] or []
        # This command does not use a formatter.  Maybe it should.
        if chooser and chooser.debug_info:
            return str("\n".join(chooser.debug_info + out_array))
        return str("\n".join(chooser.messages + out_array))
