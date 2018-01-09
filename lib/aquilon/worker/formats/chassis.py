# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013,2014,2016  Contributor
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
"""Chassis formatter."""

from aquilon.aqdb.model import Chassis
from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.hardware_entity import HardwareEntityFormatter


class ChassisFormatter(HardwareEntityFormatter):
    def add_details_for_slot(self, slot):
        hw = getattr(slot, slot.slot_type)
        if hw:
            if hw.primary_name:
                hostname = hw.primary_name
            else:
                hostname = "no hostname"
            return "Slot #%d (type: %s): %s (%s)" % (slot.slot_number,
                                                     slot.slot_type,
                                                     hw.label, hostname)
        return "Slot #%d (type: %s): Empty" % (slot.slot_number,
                                               slot.slot_type)

    def format_raw(self, chassis, indent="", embedded=True,
                   indirect_attrs=True):
        details = [super(ChassisFormatter, self).format_raw(chassis, indent, embedded=embedded,
                                                            indirect_attrs=indirect_attrs)]

        for slot in (chassis.machine_slots + chassis.network_device_slots):
            details.append(indent + "  " + self.add_details_for_slot(slot))

        return "\n".join(details)

ObjectFormatter.handlers[Chassis] = ChassisFormatter()
