# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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
"""Contains the logic for `aq add domain`."""


import os

from aquilon.exceptions_ import (AuthorizationException, ArgumentError)
from aquilon.server.broker import BrokerCommand
from aquilon.aqdb.model import Domain
from aquilon.server.dbwrappers.user_principal import (
        get_or_create_user_principal)
from aquilon.server.processes import run_command
import re

class CommandAddDomain(BrokerCommand):

    required_parameters = ["domain"]

    def render(self, session, logger, domain, user, **arguments):
        dbuser = get_or_create_user_principal(session, user)
        if not dbuser:
            raise AuthorizationException("Cannot create a domain without"
                    + " an authenticated connection.")

        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(domain)):
            raise ArgumentError("domain name '%s' is not valid"%domain)

        # For now, succeed without error if the domain already exists.
        dbdomain = session.query(Domain).filter_by(name=domain).first()
        if not dbdomain:
            compiler = self.config.get("broker", "domain_default_panc")
            dbdomain = Domain(name=domain, owner=dbuser, compiler=compiler)
            session.add(dbdomain)
            session.flush()
            session.refresh(dbdomain)
        domaindir = os.path.join(self.config.get("broker", "templatesdir"),
                dbdomain.name)
        # FIXME: If this command fails, should the domain entry be
        # created in the database anyway?
        git_env={"PATH":"%s:%s" % (self.config.get("broker", "git_path"),
            os.environ.get("PATH", ""))}
        run_command(["git", "clone", self.config.get("broker", "kingdir"),
                     domaindir], env=git_env, logger=logger)
        # The 1.0 code notes that this should probably be done as a
        # hook in git... just need to make sure it runs.
        run_command(["git-update-server-info"], env=git_env, path=domaindir,
                    logger=logger)
        return
