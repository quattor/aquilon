# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""MachineSpecs formatter."""


from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import MachineSpecs


class MachineSpecsFormatter(ObjectFormatter):
    def format_raw(self, machine_specs, indent=""):
        details = [indent + "MachineSpecs for %s %s:" %
                (machine_specs.model.vendor.name, machine_specs.model.name)]
        details.append(indent + "  Cpu: %s x %d" % (machine_specs.cpu.name,
            machine_specs.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine_specs.memory)
        details.append(indent + "  NIC count: %d" % machine_specs.nic_count)
        if machine_specs.nic_model:
            details.append(indent + "  NIC Vendor: %s Model: %s" %
                           (machine_specs.nic_model.vendor.name,
                            machine_specs.nic_model.name))
        details.append(indent + "  Disk: %s %d GB %s (%s)" %
                       (machine_specs.disk_name,
                        machine_specs.disk_capacity,
                        machine_specs.controller_type,
                        machine_specs.disk_type))
        # TODO: there is no way to set the comments on MachineSpecs right now
        if machine_specs.comments:  # pragma: no cover
            details.append(indent + "  Comments: %s" % machine_specs.comments)
        return "\n".join(details)

ObjectFormatter.handlers[MachineSpecs] = MachineSpecsFormatter()
