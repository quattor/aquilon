# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013,2014,2015,2016  Contributor
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
"""Contains the logic for `aq add machine`."""

from sqlalchemy.orm import joinedload, subqueryload

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import Chassis, ChassisSlot, Model, Machine
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.machine import create_machine
from aquilon.worker.dbwrappers.resources import get_resource_holder
from aquilon.worker.templates.base import Plenary, PlenaryCollection


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    def render(self, session, logger, machine, model, vendor, serial, uuid,
               chassis, slot, cpuname, cpuvendor, cpucount, memory, recipe,
               cluster, metacluster, vmhost, uri, comments, **arguments):
        dblocation = get_location(session,
                                  query_options=[subqueryload('parents'),
                                                 joinedload('parents.dns_maps')],
                                  **arguments)
        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            if slot is None:
                raise ArgumentError("The --chassis option requires a --slot.")
            if dblocation and dblocation != dbchassis.location:
                raise ArgumentError("{0} conflicts with chassis location "
                                    "{1}.".format(dblocation, dbchassis.location))
            dblocation = dbchassis.location
        elif slot is not None:
            raise ArgumentError("The --slot option requires a --chassis.")

        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if not dbmodel.model_type.isMachineType():
            raise ArgumentError("The add_machine command cannot add machines "
                                "of type %s." % str(dbmodel.model_type))

        vmholder = None

        if cluster or metacluster or vmhost:
            if not dbmodel.model_type.isVirtualMachineType():
                raise ArgumentError("{0} is not a virtual machine."
                                    .format(dbmodel))

            # TODO: do we need VMs inside resource groups?
            vmholder = get_resource_holder(session, logger, hostname=vmhost,
                                           cluster=cluster,
                                           metacluster=metacluster,
                                           resgroup=None, compel=False)

            if vmholder.holder_object.status.name == 'decommissioned':
                raise ArgumentError("Cannot add virtual machines to "
                                    "decommissioned holders.")

            if hasattr(vmholder.holder_object, 'location_constraint'):
                container_loc = vmholder.holder_object.location_constraint
            else:
                container_loc = vmholder.holder_object.hardware_entity.location

            if dblocation and dblocation != container_loc:
                raise ArgumentError("Cannot override container location {0} "
                                    "with location {1}.".format(container_loc,
                                                                dblocation))
            dblocation = container_loc
        elif dbmodel.model_type.isVirtualMachineType():
            raise ArgumentError("Virtual machines must be assigned to a "
                                "cluster or a host.")

        Machine.get_unique(session, machine, preclude=True)
        dbmachine = create_machine(self.config, session, logger, machine,
                                   dblocation, dbmodel, cpuname=cpuname,
                                   cpuvendor=cpuvendor, cpucount=cpucount,
                                   memory=memory, uri=uri, serial=serial,
                                   uuid=uuid, recipe=recipe, vmholder=vmholder,
                                   comments=comments)

        if chassis:
            # FIXME: Are virtual machines allowed to be in a chassis?
            dbslot = session.query(ChassisSlot).filter_by(chassis=dbchassis,
                                                          slot_number=slot).first()
            if dbslot and dbslot.machine:
                raise ArgumentError("{0} slot {1} already has machine "
                                    "{2}.".format(dbchassis, slot,
                                                  dbslot.machine.label))
            if not dbslot:
                dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
            dbslot.machine = dbmachine
            session.add(dbslot)

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.add(dbmachine)
        if vmholder:
            plenaries.add(vmholder.holder_object)
            plenaries.add(dbmachine.vm_container)

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenaries.write()
        return
