# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010,2011,2012  Contributor
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
"""Contains the logic for `aq grant root access`."""

from aquilon.aqdb.model import Personality, User, NetGroupWhiteList
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.templates.personality import PlenaryPersonality


class CommandGrantRootAccess(BrokerCommand):

    def _update_dbobj(self, obj, dbuser=None, dbnetgroup=None):
        if dbuser and dbuser not in obj.root_users:
            obj.root_users.append(dbuser)
            return
        if dbnetgroup and dbnetgroup not in obj.root_netgroups:
            obj.root_netgroups.append(dbnetgroup)

    def render(self, session, logger, username, netgroup, personality,
               archetype, **arguments):

        dbobj = Personality.get_unique(session, name=personality,
                                       archetype=archetype, compel=True)
        if username:
            dbuser = User.get_unique(session, name=username,
                                     compel=True)
            self._update_dbobj(dbobj, dbuser=dbuser)
        elif netgroup:
            dbng = NetGroupWhiteList.get_unique(session, name=netgroup,
                                                compel=True)
            self._update_dbobj(dbobj, dbnetgroup=dbng)

        session.flush()

        plenary = PlenaryPersonality(dbobj, logger=logger)
        plenary.write()

        return
