# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009  Contributor
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


from aquilon.server.formats.formatters import ObjectFormatter
from aquilon.aqdb.model import Chassis


class ChassisFormatter(ObjectFormatter):
    def format_raw(self, chassis, indent=""):
        details = [indent + "%s: %s" %
                (chassis.chassis_hw.model.machine_type.capitalize(),
                 chassis.fqdn)]
        if chassis.ip:
            details.append(indent + "  IP: %s" % chassis.ip)
        details.append(self.redirect_raw(chassis.chassis_hw.location,
                                         indent + "  "))
        details.append(self.redirect_raw(chassis.chassis_hw.model,
                                         indent + "  "))
        if chassis.chassis_hw.serial_no:
            details.append(indent + "  Serial: %s" %
                           chassis.chassis_hw.serial_no)
        for slot in chassis.slots:
            if slot.machine:
                details.append(indent + "  Slot #%d: %s" % (slot.slot_number,
                                                            slot.machine.name))
            else:
                details.append(indent + "  Slot #%d Unknown" % slot.slot_number)
        for i in chassis.chassis_hw.interfaces:
            details.append(self.redirect_raw(i, indent + "  "))
        if chassis.comments:
            details.append(indent + "  Comments: %s" % chassis.comments)
        return "\n".join(details)

ObjectFormatter.handlers[Chassis] = ChassisFormatter()
