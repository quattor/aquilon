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
"""Contains the logic for `aq add model`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Vendor, Model, MachineSpecs, Cpu


class CommandAddModel(BrokerCommand):

    required_parameters = ["model", "vendor", "type"]

    def render(self, session, model, vendor, type, cpuname, cpuvendor, cpuspeed,
               cpunum, memory, disktype, diskcontroller, disksize,
               nics, nicmodel, nicvendor,
               comments, **arguments):
        dbvendor = Vendor.get_unique(session, vendor, compel=True)
        Model.get_unique(session, name=model, vendor=dbvendor, preclude=True)

        # Specifically not allowing new models to be added that are of
        # type aurora_node - that is only meant for the dummy aurora_model.
        allowed_types = ["blade", "rackmount", "workstation", "switch",
                         "chassis", "virtual_machine", "nic", "virtual_appliance"]

        if type not in allowed_types:
            raise ArgumentError("The model's machine type must be one of: %s." %
                                ", ".join(allowed_types))

        dbmodel = Model(name=model, vendor=dbvendor, machine_type=type,
                        comments=comments)
        session.add(dbmodel)
        session.flush()

        if cpuname or cpuvendor or cpuspeed is not None:
            dbcpu = Cpu.get_unique(session, name=cpuname, vendor=cpuvendor,
                                   speed=cpuspeed, compel=True)
            if nicmodel or nicvendor:
                dbnic = Model.get_unique(session, machine_type='nic',
                                         name=nicmodel, vendor=nicvendor,
                                         compel=True)
            else:
                dbnic = Model.default_nic_model(session)
            dbmachine_specs = MachineSpecs(model=dbmodel, cpu=dbcpu,
                                           cpu_quantity=cpunum, memory=memory,
                                           disk_type=disktype,
                                           controller_type=diskcontroller,
                                           disk_capacity=disksize,
                                           nic_count=nics, nic_model=dbnic)
            session.add(dbmachine_specs)
        return
