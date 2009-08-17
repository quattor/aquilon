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


from aquilon.aqdb.model import OperatingSystem
from aquilon.server.broker import BrokerCommand
from aquilon.server.dbwrappers.os import get_os_query
from aquilon.server.dbwrappers.archetype import get_archetype
from aquilon.exceptions_ import ArgumentError
import re


class CommandAddOS(BrokerCommand):

    required_parameters = [ "osname", "version", "archetype" ]

    def render(self, session, osname, version, archetype, **arguments):
        valid = re.compile('^[a-zA-Z0-9_.-]+$')
        if (not valid.match(osname)):
            raise ArgumentError("OS name '%s' is not valid" % osname)
        if not valid.match(version):
            raise ArgumentError("OS version '%s' is not valid" % version)

        q = get_os_query(session, osname, version, archetype)
        existing = q.all()

        if existing:
            raise ArgumentError(
                "%s version %s already exists in archetype %s" % (osname,
                                                                  version,
                                                                  archetype))

        else:
            dbarchetype=get_archetype(session, archetype)
            dbos = OperatingSystem(name=osname, version=version,
                                   archetype=dbarchetype)
            #FIXME: why no comments?
            session.add(dbos)

        return
