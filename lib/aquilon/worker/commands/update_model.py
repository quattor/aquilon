# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2010,2011,2013,2014,2015,2016,2017  Contributor
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
"""Contains the logic for `aq update model`."""


from aquilon.exceptions_ import ArgumentError, UnimplementedError
from aquilon.aqdb.types import CpuType, NicType
from aquilon.aqdb.model import (Vendor, Model, MachineSpecs, Machine, Disk,
                                HardwareEntity, Interface)
from aquilon.worker.broker import BrokerCommand
from sqlalchemy.orm import object_session, contains_eager
from aquilon.worker.dbwrappers.change_management import ChangeManagement


class CommandUpdateModel(BrokerCommand):
    requires_plenaries = True

    required_parameters = ["model", "vendor"]

    # Quick hash of the arguments this method takes to the corresponding
    # aqdb label.
    argument_lookup = {'cpuname': 'name', 'cpuvendor': 'vendor',
                       'cpunum': 'cpu_quantity',
                       'memory': 'memory', 'disktype': 'disk_type',
                       'diskcontroller': 'controller_type',
                       'disksize': 'disk_capacity',
                       'nicmodel': 'name', 'nicvendor': 'vendor'}

    def render(self, session, plenaries, model, vendor, newvendor,
               comments, update_existing_machines, user, justification, reason,
               logger, **arguments):
        for (arg, value) in arguments.items():
            # Cleaning the strings isn't strictly necessary but allows
            # for simple equality checks below and removes the need to
            # call refresh().
            if arg in ['newvendor', 'cpuname', 'cpuvendor', 'disktype', 'diskcontroller',
                       'nicmodel', 'nicvendor']:
                if value is not None:
                    arguments[arg] = value.lower().strip()

        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if not update_existing_machines and newvendor:
            raise ArgumentError("Cannot update vendor without "
                                "updating any existing machines.")

        if update_existing_machines:
            # Validate ChangeManagement
            q = session.query(Machine).filter_by(model=dbmodel)
            cm = ChangeManagement(session, user, justification, reason, logger, self.command, **arguments)
            cm.consider(q)
            cm.validate()

        dbmachines = set()

        # The sub-branching here is a little difficult to read...
        # Basically, there are three different checks to handle
        # setting a new vendor, a new name, or both.
        if newvendor:
            dbnewvendor = Vendor.get_unique(session, newvendor, compel=True)
            Model.get_unique(session, name=dbmodel.name,
                             vendor=dbnewvendor, preclude=True)
            dbmodel.vendor = dbnewvendor
            q = session.query(HardwareEntity).filter_by(model=dbmodel)
            dbmachines.update(q)

        # For now, can't update model_type.  There are too many spots
        # that special case things like aurora_node or virtual_machine to
        # know that the transistion is safe.  If there is enough need we
        # can always add those transitions later.
        if arguments['machine_type'] is not None:
            raise UnimplementedError("Cannot (yet) change a model's "
                                     "machine type.")

        if comments is not None:
            dbmodel.comments = comments
            # The comments also do not affect the templates.

        cpu_args = ['cpuname', 'cpuvendor']
        cpu_info = {self.argument_lookup[arg]: arguments[arg]
                    for arg in cpu_args}
        cpu_values = [v for v in cpu_info.values() if v is not None]
        nic_args = ['nicmodel', 'nicvendor']
        nic_info = {self.argument_lookup[arg]: arguments[arg]
                    for arg in nic_args}
        nic_values = [v for v in nic_info.values() if v is not None]
        spec_args = ['cpunum', 'memory', 'disktype', 'diskcontroller',
                     'disksize']
        specs = {self.argument_lookup[arg]: arguments[arg]
                 for arg in spec_args}
        spec_values = [v for v in specs.values() if v is not None]

        if not dbmodel.machine_specs:
            if cpu_values or nic_values or spec_values:
                # You can't add a non-machine model with machine_specs
                # thus we only need to check here if you try and update
                if not dbmodel.model_type.isMachineType():
                    raise ArgumentError("Machine specfications are only valid"
                                        " for machine types")
                if not cpu_values or len(spec_values) < len(spec_args):
                    raise ArgumentError("Missing required parameters to store "
                                        "machine specs for the model.  Please "
                                        "give all CPU, disk, RAM, and NIC "
                                        "count information.")
                dbcpu = Model.get_unique(session, compel=True,
                                         model_type=CpuType.Cpu, **cpu_info)
                if nic_values:
                    dbnic = Model.get_unique(session, compel=True,
                                             model_type=NicType.Nic, **nic_info)
                else:
                    dbnic = Model.default_nic_model(session)
                dbmachine_specs = MachineSpecs(model=dbmodel, cpu_model=dbcpu,
                                               nic_model=dbnic, **specs)
                session.add(dbmachine_specs)

        # Anything below that updates specs should have been verified above.

        if cpu_values:
            dbcpu = Model.get_unique(session, compel=True,
                                     model_type=CpuType.Cpu, **cpu_info)
            self.update_machine_specs(model=dbmodel, dbmachines=dbmachines,
                                      attr='cpu_model', value=dbcpu,
                                      fix_existing=update_existing_machines)

        for arg in ['memory', 'cpunum']:
            if arguments[arg] is not None:
                self.update_machine_specs(model=dbmodel, dbmachines=dbmachines,
                                          attr=self.argument_lookup[arg],
                                          value=arguments[arg],
                                          fix_existing=update_existing_machines)

        if arguments['disktype']:
            if update_existing_machines:
                raise ArgumentError("Please do not specify "
                                    "--update_existing_machines to change "
                                    "the model disktype.  This cannot "
                                    "be converted automatically.")
            dbmodel.machine_specs.disk_type = arguments['disktype']

        for arg in ['diskcontroller', 'disksize']:
            if arguments[arg] is not None:
                self.update_disk_specs(model=dbmodel, dbmachines=dbmachines,
                                       attr=self.argument_lookup[arg],
                                       value=arguments[arg],
                                       fix_existing=update_existing_machines)

        if nic_values:
            dbnic = Model.get_unique(session, compel=True, **nic_info)
            self.update_interface_specs(model=dbmodel, dbmachines=dbmachines,
                                        value=dbnic,
                                        fix_existing=update_existing_machines)

        session.flush()

        plenaries.add(dbmachines)
        plenaries.write()

        return

    def update_machine_specs(self, model, dbmachines,
                             attr=None, value=None, fix_existing=False):
        session = object_session(model)
        if fix_existing:
            oldattr = getattr(model.machine_specs, attr)
            filters = {'model': model, attr: oldattr}
            q = session.query(Machine).filter_by(**filters)
            for dbmachine in q:
                setattr(dbmachine, attr, value)
                dbmachines.add(dbmachine)

        setattr(model.machine_specs, attr, value)

    def update_disk_specs(self, model, dbmachines,
                          attr=None, value=None, fix_existing=False):
        session = object_session(model)
        if fix_existing:
            oldattr = getattr(model.machine_specs, attr)
            # disk_capacity => capacity
            disk_attr = attr.replace('disk_', '')
            filters = {disk_attr: oldattr}
            q = session.query(Disk)
            q = q.filter_by(**filters)
            q = q.join(Machine)
            q = q.filter_by(model=model)
            for dbdisk in q:
                setattr(dbdisk, disk_attr, value)
                dbmachines.add(dbdisk.machine)

        setattr(model.machine_specs, attr, value)

    def update_interface_specs(self, model, dbmachines, value=None,
                               fix_existing=False):
        session = object_session(model)
        if fix_existing:
            old_nic_model = model.machine_specs.nic_model
            q = session.query(Interface)
            # Skip interfaces where the model was set explicitely to something
            # other than the default
            q = q.filter(Interface.model == old_nic_model)
            q = q.join(HardwareEntity)
            q = q.filter(HardwareEntity.model == model)
            q = q.options(contains_eager('hardware_entity'))
            for dbiface in q:
                dbiface.model = value
                dbmachines.add(dbiface.hardware_entity)

        model.machine_specs.nic_model = value
