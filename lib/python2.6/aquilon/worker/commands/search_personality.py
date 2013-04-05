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
"""Contains the logic for `aq show personality`."""


from sqlalchemy.orm import joinedload, subqueryload, contains_eager
from sqlalchemy.sql import or_

from aquilon.aqdb.model import (Archetype, Personality, HostEnvironment,
                                PersonalityGrnMap)
from aquilon.worker.dbwrappers.grn import lookup_grn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.formats.personality import (PersonalityList,
                                                SimplePersonalityList)


class CommandSearchPersonality(BrokerCommand):

    required_parameters = []

    def render(self, session, personality, archetype, grn, eon_id,
               host_environment, config_override, fullinfo, **arguments):
        q = session.query(Personality)
        if archetype:
            dbarchetype = Archetype.get_unique(session, archetype, compel=True)
            q = q.filter_by(archetype=dbarchetype)

        if personality:
            q = q.filter_by(name=personality)

        if config_override:
            q = q.filter_by(config_override=True)

        if host_environment:
            host_env = HostEnvironment.get_unique(session, host_environment, compel=True)
            q = q.filter_by(host_environment=host_env)

        if grn or eon_id:
            dbgrn = lookup_grn(session, grn, eon_id, autoupdate=False)
            q = q.outerjoin(PersonalityGrnMap)
            q = q.filter(or_(Personality.owner_eon_id == dbgrn.eon_id,
                             PersonalityGrnMap.eon_id == dbgrn.eon_id))

        q = q.join(Archetype)
        q = q.order_by(Archetype.name, Personality.name)
        q = q.options(contains_eager('archetype'))

        if fullinfo:
            q = q.options(subqueryload('services'),
                          subqueryload('grns'),
                          subqueryload('features'),
                          joinedload('features.feature'),
                          joinedload('cluster_infos'))
            return PersonalityList(q.all())
        else:
            return SimplePersonalityList(q.all())
