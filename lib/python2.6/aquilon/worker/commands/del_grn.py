# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
"""Contains the logic for `aq del grn`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Host, Personality, HostGrnMap, PersonalityGrnMap
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.grn import lookup_grn


class CommandDelGrn(BrokerCommand):

    def render(self, session, logger, grn, eon_id, **arguments):
        dbgrn = lookup_grn(session, grn, eon_id, logger=logger,
                           config=self.config, usable_only=False)

        q1 = session.query(Host)
        q1 = q1.filter_by(owner_eon_id=dbgrn.eon_id)
        q2 = session.query(HostGrnMap)
        q2 = q2.filter_by(eon_id=dbgrn.eon_id)
        if q1.first() or q2.first():
            raise ArgumentError("GRN %s is still used by hosts, and "
                                "cannot be deleted." % dbgrn.grn)

        q1 = session.query(Personality)
        q1 = q1.filter_by(owner_eon_id=dbgrn.eon_id)
        q2 = session.query(PersonalityGrnMap)
        q2 = q2.filter_by(eon_id=dbgrn.eon_id)
        if q1.first() or q2.first():
            raise ArgumentError("GRN %s is still used by personalities, "
                                "and cannot be deleted." % dbgrn.grn)

        session.delete(dbgrn)
        session.flush()
        return
