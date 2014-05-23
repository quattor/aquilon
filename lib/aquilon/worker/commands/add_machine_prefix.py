# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains a wrapper for `aq add machine --prefix`."""


from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_machine import CommandAddMachine
from aquilon.worker.dbwrappers.search import search_next
from aquilon.aqdb.model import Machine
from aquilon.aqdb.column_types import AqStr


class CommandAddMachinePrefix(CommandAddMachine):

    required_parameters = ["prefix", "model"]

    def render(self, session, logger, prefix, **args):
        prefix = AqStr.normalize(prefix)
        # We don't have a good high-level object to lock here to prevent
        # concurrent allocations, so we'll lock all existing Machine objects
        # matching the prefix
        result = search_next(session=session, cls=Machine, attr=Machine.label,
                             value=prefix, start=None, pack=None, locked=True)
        machine = '%s%d' % (prefix, result)
        args['machine'] = machine
        CommandAddMachine.render(self, session, logger, **args)

        logger.info("Selected hardware label %s" % machine)
        self.audit_result(session, 'machine', machine, **args)
        return machine
