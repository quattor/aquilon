# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Machine formatter."""


from aquilon import const
from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.server.formats.list import ListFormatter
from aquilon.aqdb.model import Machine


class MachineInterfacePair(tuple):
    """Encapsulates a (machine, selected interface) pair"""
    pass


class MachineInterfacePairFormatter(ObjectFormatter):
    def csv_fields(self, item):
        machine = item[0]
        interface = item[1]

        details = [machine.name, machine.location.rack.name,
                   machine.location.building.name, machine.model.vendor.name,
                   machine.model.name, machine.serial_no]
        if interface:
            details.extend([interface.name, interface.mac])
            if interface.system:
                details.append(interface.system.ip)
            else:
                details.append(None)
        else:
            details.extend([None, None, None])
        return details

ObjectFormatter.handlers[MachineInterfacePair] = MachineInterfacePairFormatter()


class MachineFormatter(ObjectFormatter):
    def format_raw(self, machine, indent=""):
        details = [indent + "%s: %s" %
                (machine.model.machine_type.capitalize(), machine.name)]
        if machine.host:
            details.append(indent + "  Allocated to host: %s [%s]"
                    % (machine.host.fqdn, machine.host.ip))
        if machine.cluster:
            details.append(indent + \
                           "  Hosted by {0:c}: {0.name}".format(machine.cluster))
        for manager in machine.manager:
            details.append(indent + "  Manager: %s [%s]" % (manager.fqdn,
                                                            manager.ip))
        for dbauxiliary in machine.auxiliaries:
            details.append(indent + "  Auxiliary: %s [%s]" % (
                           dbauxiliary.fqdn, dbauxiliary.ip))
        # This is a bit of a hack.  Delegating out to the standard location
        # formatter now spews too much information about chassis.  Maybe
        # that will change when chassis has a corresponding hardware type.
        for location_type in const.location_types:
            if getattr(machine.location, location_type, None) is not None:
                loc = getattr(machine.location, location_type)
                details.append(indent + "  {0:c}: {0.name}".format(loc))
                if location_type == 'rack':
                    details.append(indent + "    Row: %s" %
                                   machine.location.rack.rack_row)
                    details.append(indent + "    Column: %s" %
                                   machine.location.rack.rack_column)
        for slot in machine.chassis_slot:
            details.append(indent + "  {0:c}: {0.fqdn}".format(slot.chassis))
            details.append(indent + "  Slot: %d" % slot.slot_number)
        details.append(indent + "  {0:c}: {0.name} {1:c}: {1.name}".format(
            machine.model.vendor, machine.model))
        details.append(indent + "  Cpu: %s x %d" %
                (machine.cpu, machine.cpu_quantity))
        details.append(indent + "  Memory: %d MB" % machine.memory)
        if machine.serial_no:
            details.append(indent + "  Serial: %s" % machine.serial_no)
        for d in machine.disks:
            extra = d.disk_type
            if d.disk_type == "nas" and d.service_instance:
                extra = extra + " from " + d.service_instance.name
            details.append(indent + "  Disk: %s %d GB %s (%s)"
                    % (d.device_name, d.capacity, d.controller_type,
                       extra))
        for i in machine.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if machine.comments:
            details.append(indent + "  Comments: %s" % machine.comments)
        return "\n".join(details)

    def get_header(self):
        """This is just an idea... not used anywhere (yet?)."""
        return "machine,rack,building,vendor,model,serial,interface,mac,ip"

    def csv_tolist(self, machine):
        if machine.interfaces:
            return [MachineInterfacePair((machine, i))
                    for i in machine.interfaces]
        else:
            return [MachineInterfacePair((machine, None))]

ObjectFormatter.handlers[Machine] = MachineFormatter()


class SimpleMachineList(list):
    pass


class SimpleMachineListFormatter(ListFormatter):
    def format_raw(self, smlist, indent=""):
        return str("\n".join([indent + machine.name for machine in smlist]))

ObjectFormatter.handlers[SimpleMachineList] = SimpleMachineListFormatter()


class MachineMacList(list):
    """ Holds MAC, machine-name [, hostname] """
    pass


class MachineMacListFormatter(ListFormatter):
    def csv_fields(self, result):
        return result

ObjectFormatter.handlers[MachineMacList] = MachineMacListFormatter()
