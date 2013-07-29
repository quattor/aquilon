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
"""Contains the logic for `aq add grn`."""

from aquilon.aqdb.model import Grn
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611


class CommandAddGrn(BrokerCommand):

    required_parameters = ["grn", "eon_id"]

    def render(self, session, grn, eon_id, disabled, **arguments):
        Grn.get_unique(session, grn=grn, preclude=True)
        Grn.get_unique(session, eon_id=eon_id, preclude=True)

        if disabled is None:
            disabled = False
        dbgrn = Grn(grn=grn, eon_id=eon_id, disabled=disabled)
        session.add(dbgrn)

        session.flush()
        return
