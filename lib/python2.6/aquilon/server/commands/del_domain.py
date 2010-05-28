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
"""Contains the logic for `aq del domain`."""


import os

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand
from aquilon.server.processes import remove_dir
from aquilon.server.locks import lock_queue, CompileKey
from aquilon.server.templates.domain import TemplateDomain
from aquilon.aqdb.model import Domain


class CommandDelDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, **arguments):
        # FIXME: This will fail if the domain does not exist.  We might
        # want to allow the directory to be deleted anyway, assuming it
        # is a valid domain name and az_check passes.
        dbdomain = Domain.get_unique(session, domain, compel=True)
        session.refresh(dbdomain)
        if dbdomain.hosts:
            raise ArgumentError("Cannot delete domain %s while hosts are still attached."
                    % dbdomain.name)
        session.delete(dbdomain)

        # Technically we shouldn't need a lock here at all, since
        # nothing else should be using this domain.
        domain = TemplateDomain(dbdomain, logger=logger)
        key = CompileKey(domain=dbdomain.name, logger=logger)
        try:
            lock_queue.acquire(key)
            for dir in domain.directories():
                remove_dir(dir, logger=logger)
        finally:
            lock_queue.release(key)

        return