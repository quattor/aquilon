# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014  Contributor
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
"""Contains the logic for `aq del auxiliary`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import ARecord
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.del_interface_address import \
    CommandDelInterfaceAddress


class CommandDelAuxiliary(CommandDelInterfaceAddress):

    required_parameters = ["auxiliary"]

    def render(self, session, logger, auxiliary, **arguments):
        # Check dependencies, translate into user-friendly message
        dbauxiliary = ARecord.get_unique(session, fqdn=auxiliary, compel=True)

        is_aux = True
        if not dbauxiliary.assignments or len(dbauxiliary.assignments) > 1:
            is_aux = False
        else:
            assignment = dbauxiliary.assignments[0]
            dbinterface = assignment.interface

            if assignment.ip == dbinterface.hardware_entity.primary_ip:
                is_aux = False
            if assignment.interface.interface_type == 'management':
                is_aux = False

        if not is_aux:
            raise ArgumentError("{0:a} is not an auxiliary.".format(dbauxiliary))

        return super(CommandDelAuxiliary, self).render(session, logger,
                                                       machine=dbinterface.hardware_entity.label,
                                                       chassis=None, network_device=None,
                                                       interface=dbinterface.name,
                                                       fqdn=auxiliary,
                                                       ip=assignment.ip,
                                                       label=None,
                                                       keep_dns=False,
                                                       network_environment=None,
                                                       **arguments)
