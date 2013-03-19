# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2013  Contributor
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
"""Chassis formatter."""


import re

from sqlalchemy.orm.session import object_session

from aquilon.worker.formats.formatters import ObjectFormatter
from aquilon.worker.formats.list import ListFormatter
from aquilon.aqdb.model import Chassis

chassis_re = re.compile("^(.*)c(\d+)n(\d+)$")


class ChassisFormatter(ObjectFormatter):
    def format_raw(self, chassis, indent=""):
        details = [indent + "%s: %s" % (chassis.model.machine_type.capitalize(),
                                        chassis.label)]
        if chassis.primary_name:
            details.append(indent + "  Primary Name: "
                           "{0:a}".format(chassis.primary_name))
        details.append(self.redirect_raw(chassis.location, indent + "  "))
        details.append(self.redirect_raw(chassis.model, indent + "  "))
        if chassis.serial_no:
            details.append(indent + "  Serial: %s" %
                           chassis.serial_no)
        for slot in chassis.slots:
            if slot.machine:
                details.append(indent + "  Slot #%d: %s" % (slot.slot_number,
                                                            slot.machine.label))
            else:
                details.append(indent + "  Slot #%d Unknown" % slot.slot_number)
        for i in chassis.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if chassis.comments:
            details.append(indent + "  Comments: %s" % chassis.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Chassis] = ChassisFormatter()


class MissingChassisList(list):
    pass


class MissingChassisListFormatter(ListFormatter):
    def format_raw(self, machines, indent=""):
        if machines:
            session = object_session(machines[0])

        commands = []
        for machine in machines:
            # Try to guess the name of the chassis
            result = chassis_re.match(machine.label)
            if result:
                chassis = "%sc%s" % (result.group(1), result.group(2))
                slot = result.group(3)

                dbchassis = Chassis.get_unique(session, chassis)
                if not dbchassis and machine.primary_name:
                    fqdn = "%s.%s" % (chassis,
                                      machine.primary_name.fqdn.dns_domain.name)
                    commands.append("aq add chassis --chassis '%s' "
                                    "--rack 'RACK' --model 'MODEL'" % fqdn)
            else:
                chassis = 'CHASSIS'
                slot = 'SLOT'

            commands.append("aq update machine --machine '%s' "
                            "--chassis '%s' --slot '%s'" % (machine.label,
                                                            chassis, slot))
        return "\n".join(commands)

ObjectFormatter.handlers[MissingChassisList] = MissingChassisListFormatter()
