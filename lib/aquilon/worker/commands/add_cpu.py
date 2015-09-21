# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2015  Contributor
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
"""Contains the logic for `aq add cpu`."""

from aquilon.aqdb.types import CpuType
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.commands.add_model import CommandAddModel


class CommandAddCpu(CommandAddModel):

    required_parameters = ["cpu", "vendor"]

    def render(self, cpu, **arguments):
        self.deprecated_command("The add_cpu command is deprecated. Please "
                                "use add_model instead.", **arguments)
        return super(CommandAddCpu, self).render(model=cpu, type=CpuType.Cpu,
                                                 cpuname=None, cpuvendor=None,
                                                 cpunum=None, memory=None,
                                                 disktype=None,
                                                 diskcontroller=None,
                                                 disksize=None, nics=None,
                                                 nicmodel=None, nicvendor=None,
                                                 **arguments)
