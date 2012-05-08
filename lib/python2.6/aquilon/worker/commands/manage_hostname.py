# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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


from aquilon.exceptions_ import IncompleteError, ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.branch import get_branch_and_author
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey


class CommandManageHostname(BrokerCommand):

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, domain, sandbox, **arguments):
        (dbbranch, dbauthor) = get_branch_and_author(session, logger,
                                                     domain=domain,
                                                     sandbox=sandbox,
                                                     compel=True)

        if hasattr(dbbranch, "allow_manage") and not dbbranch.allow_manage:
            raise ArgumentError("Managing hosts to {0:l} is not allowed."
                                .format(dbbranch))

        dbhost = hostname_to_host(session, hostname)
        if dbhost.cluster:
            raise ArgumentError("Cluster nodes must be managed at the "
                                "cluster level; this host is a member of "
                                "{0}.".format(dbhost.cluster))

        old_branch = dbhost.branch.name

        dbhost.branch = dbbranch
        dbhost.sandbox_author = dbauthor
        session.add(dbhost)
        session.flush()
        plenary_host = PlenaryHost(dbhost, logger=logger)

        # We're crossing domains, need to lock everything.
        # XXX: There's a directory per domain.  Do we need subdirectories
        # for different authors for a sandbox?
        key = CompileKey(logger=logger)
        try:
            lock_queue.acquire(key)

            plenary_host.stash()
            plenary_host.cleanup(old_branch, locked=True)

            # Now we recreate the plenary to ensure that the domain is ready
            # to compile, however (esp. if there was no existing template), we
            # have to be aware that there might not be enough information yet
            # with which we can create a template
            try:
                plenary_host.write(locked=True)
            except IncompleteError:
                # This template cannot be written, we leave it alone
                # It would be nice to flag the state in the the host?
                pass
        except:
            # This will not restore the cleaned up files.  That's OK.
            # They will be recreated as needed.
            plenary_host.restore_stash()
            raise
        finally:
            lock_queue.release(key)

        return
