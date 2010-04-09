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
"""Contains the logic for `aq make cluster`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Cluster
from aquilon.server.templates.domain import TemplateDomain
from aquilon.server.templates.base import compileLock, compileRelease
from aquilon.server.services import Chooser


class CommandMakeCluster(BrokerCommand):

    required_parameters = ["cluster"]

    def render(self, session, logger, cluster, keepbindings, **arguments):
        dbcluster = Cluster.get_unique(session, cluster)
        if not dbcluster:
            raise NotFoundException("Cluster '%s' not found." % cluster)

        chooser = None
        try:
            compileLock(logger=logger)

            if not dbcluster.personality.archetype.is_compileable:
                raise ArgumentError("Cluster %s is not a compilable archetype "
                                    "(%s)" %
                                    (cluster,
                                     dbcluster.personality.archetype.name))

            if keepbindings:
                required_only = False
            else:
                required_only = True
            chooser = Chooser(dbcluster, logger=logger,
                              required_only=required_only)
            chooser.set_required()
            chooser.flush_changes()
            chooser.write_plenary_templates(locked=True)

            profile_list = ["clusters/%s" % dbcluster.name]
            for h in dbcluster.hosts:
                profile_list.append(h.fqdn)

            td = TemplateDomain(dbcluster.domain, logger=logger)
            out = td.compile(session, only=" ".join(profile_list), locked=True)

        except:
            if chooser:
                chooser.restore_stash()

            # Okay, cleaned up templates, make sure the caller knows
            # we've aborted so that DB can be appropriately rollback'd.

            raise

        finally:
            compileRelease(logger=logger)

        return


