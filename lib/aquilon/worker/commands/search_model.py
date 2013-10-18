# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2012,2013  Contributor
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
"""Contains the logic for `aq search model`."""

from sqlalchemy.orm import aliased, joinedload, contains_eager

from aquilon.aqdb.model import Model, Vendor, Cpu, MachineSpecs
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.list import StringAttributeList


class CommandSearchModel(BrokerCommand):
    def render(self, session, model, vendor, machine_type, cpuname, cpuvendor, cpuspeed,
               cpunum, nicmodel, nicvendor, memory, disktype, diskcontroller,
               disksize, fullinfo, style, **arguments):
        q = session.query(Model)

        if model:
            q = q.filter(Model.name.like(model + '%'))
        if vendor:
            dbvendor = Vendor.get_unique(session, vendor)
            q = q.filter_by(vendor=dbvendor)
        if machine_type:
            q = q.filter_by(model_type=machine_type)

        # We need an explicit join for ORDER BY
        q = q.join(Vendor)
        q = q.options(contains_eager('vendor'))
        q = q.reset_joinpoint()

        if cpuname or cpuvendor or cpuspeed or cpunum or \
           nicmodel or nicvendor or \
           memory or disktype or diskcontroller or disksize:
            q = q.join((MachineSpecs, MachineSpecs.model_id == Model.id))
            q = q.options(contains_eager('machine_specs'))

            if cpuname or cpuvendor or cpuspeed is not None:
                q = q.join(Cpu)
                q = q.options(contains_eager('machine_specs.cpu'))
                if cpuname:
                    q = q.filter(Cpu.name == cpuname)
                if cpuvendor:
                    dbvendor = Vendor.get_unique(session, cpuvendor,
                                                 compel=True)
                    q = q.filter(Cpu.vendor == dbvendor)
                if cpuspeed:
                    q = q.filter(Cpu.speed == cpuspeed)
            if cpunum is not None:
                q = q.filter_by(cpu_quantity=cpunum)
            if memory is not None:
                q = q.filter_by(memory=memory)
            if nicmodel or nicvendor:
                NicModel = aliased(Model)
                q = q.join((NicModel, NicModel.id == MachineSpecs.nic_model_id))
                q = q.options(contains_eager('machine_specs.nic_model'))
                if nicmodel:
                    q = q.filter(NicModel.name == nicmodel)
                if nicvendor:
                    dbvendor = Vendor.get_unique(session, nicvendor,
                                                 compel=True)
                    q = q.filter(NicModel.vendor == dbvendor)
            if disktype:
                q = q.filter_by(disk_type=disktype)
            if diskcontroller:
                q = q.filter_by(controller_type=diskcontroller)
            if disksize:
                q = q.filter_by(disk_capacity=disksize)
        else:
            if fullinfo or style != 'raw':
                q = q.options(joinedload('machine_specs'),
                              joinedload('machine_specs.cpu'))
        q = q.order_by(Vendor.name, Model.name)

        if fullinfo or style != 'raw':
            return q.all()
        else:
            return StringAttributeList(q.all(),
                                       lambda x: "%s/%s" % (x.vendor.name,
                                                            x.name))
