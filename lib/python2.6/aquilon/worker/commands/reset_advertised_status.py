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
"""Contains the logic for `aq reset advertised status --hostname`."""


from aquilon.exceptions_ import ArgumentError, IncompleteError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.host import hostname_to_host
from aquilon.worker.templates.domain import TemplateDomain
from aquilon.worker.templates.host import PlenaryHost
from aquilon.worker.locks import lock_queue, CompileKey


class CommandResetAdvertisedStatus(BrokerCommand):
    """ reset advertised status for single host """

    required_parameters = ["hostname"]

    def render(self, session, logger, hostname, **arguments):
        dbhost = hostname_to_host(session, hostname)
        if dbhost.status.name == 'ready':
            raise ArgumentError("{0:l} is in ready status, "
                               "advertised status can be reset only "
                               "when host is in non ready state".format(dbhost))

        dbhost.advertise_status = False

        session.add(dbhost)
        session.flush()

        if dbhost.archetype.is_compileable:
            return self.compile(session, logger, dbhost)

        return

    def compile(self, session, logger, dbhost):
        """ compile plenary templates """
        plenary = PlenaryHost(dbhost, logger=logger)
        # Force a host lock as pan might overwrite the profile...
        key = CompileKey(domain=dbhost.branch.name, profile=dbhost.fqdn,
                         logger=logger)
        try:
            lock_queue.acquire(key)
            plenary.write(locked=True)
            td = TemplateDomain(dbhost.branch, dbhost.sandbox_author,
                                logger=logger)
            td.compile(session, only=dbhost.fqdn, locked=True)
        except IncompleteError:
            raise ArgumentError("Run aq make for host %s first." % dbhost.fqdn)
        except:
            plenary.restore_stash()
            raise
        finally:
            lock_queue.release(key)
