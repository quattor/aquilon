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
"""Contains the logic for `aq add machine`."""


from aquilon.exceptions_ import ArgumentError, NotFoundException
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import create_machine, get_machine
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.templates.machine import PlenaryMachineInfo
from aquilon.aqdb.model import Chassis, ChassisSlot


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    # arguments will contain one of --chassis --rack or --desk
    def render(self, session, machine, model, serial, chassis, slot,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dblocation = get_location(session, **arguments)
        if chassis:
            dbchassis = get_system(session, chassis)
            if not isinstance(dbchassis, Chassis):
                raise ArgumentError("The system '%s' is not a chassis." %
                        chassis)
            if slot is None:
                raise ArgumentError("The --chassis option requires a --slot.")
            slot = force_int("slot", slot)
            if dblocation and dblocation != dbchassis.chassis_hw.location:
                raise ArgumentError("Location %s %s conflicts with chassis location %s %s" %
                                    (dblocation.location_type,
                                     dblocation.name,
                                     dbchassis.chassis_hw.location.location_type,
                                     dbchassis.chassis_hw.location.name))
            dblocation = dbchassis.chassis_hw.location
        elif slot is not None:
            raise ArgumentError("The --slot option requires a --chassis.")

        dbmodel = get_model(session, model)

        if dbmodel.machine_type not in ['blade', 'rackmount', 'workstation',
                'aurora_node']:
            raise ArgumentError("The add_machine command cannot add machines of type '%(type)s'.  Try 'add %(type)s'." %
                    {"type": dbmodel.machine_type})


        try:
            m = get_machine(session, machine)
            raise ArgumentError("The machine '%s' already exists"%machine)
        except NotFoundException:
            pass

        dbmachine = create_machine(session, machine, dblocation, dbmodel,
                                   cpuname, cpuvendor, cpuspeed, cpucount, memory, serial)
        if chassis:
            dbslot = session.query(ChassisSlot).filter_by(chassis=dbchassis,
                    slot_number=slot).first()
            if not dbslot:
                dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
            dbslot.machine = dbmachine
            session.add(dbslot)

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write()
        return
