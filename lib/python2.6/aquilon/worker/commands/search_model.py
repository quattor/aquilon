# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2012  Contributor
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
"""Contains the logic for `aq search model`."""


from sqlalchemy.orm import aliased, joinedload, contains_eager

from aquilon.aqdb.model import Model, Vendor, Cpu, MachineSpecs
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.formats.model import SimpleModelList


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
            q = q.filter_by(machine_type=machine_type)

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
            return SimpleModelList(q.all())
