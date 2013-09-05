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
"""VirtualMachine Resource formatter."""

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.resource import ResourceFormatter
from aquilon.aqdb.model import VirtualMachine


class VirtualMachineFormatter(ResourceFormatter):
    protocol = "aqdsystems_pb2"

    def format_raw(self, vm, indent=""):
        # There will be a lot of VMs attached to a cluster, so be terse.
        dbmachine = vm.machine
        if dbmachine.primary_name:
            name = dbmachine.primary_name.fqdn
        else:
            name = "no hostname"

        # TODO: report GB instead of MB?
        return indent + "%s: %s (%s, %d MB)" % (
            vm._get_class_label(), dbmachine.label, name, dbmachine.memory)

    def format_proto(self, vm, skeleton=None):
        container = skeleton
        if not container:
            container = self.loaded_protocols[self.protocol].ResourceList()
            skeleton = container.resources.add()
        self.add_resource_data(skeleton, vm)
        return container

ObjectFormatter.handlers[VirtualMachine] = VirtualMachineFormatter()
