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
"""Contains the logic for `aq del cpu`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.aqdb.model import Cpu, MachineSpecs, Model, Vendor


class CommandDelCpu(BrokerCommand):

    required_parameters = ["cpu", "vendor", "speed"]

    def render(self, session, cpu, vendor, speed, **arguments):
        dbcpu = Cpu.get_unique(session, name=cpu, vendor=vendor, speed=speed,
                               compel=True)

        q = session.query(MachineSpecs)
        q = q.filter_by(cpu=dbcpu)
        q = q.join((Model, MachineSpecs.model_id == Model.id), Vendor)
        q = q.order_by(Vendor.name, Model.name)
        if q.count():
            models = ", ".join(["%s/%s" % (spec.model.vendor.name,
                                           spec.model.name) for spec in q])
            raise ArgumentError("{0} is still used by the following models, "
                                "and cannot be deleted: {1!s}"
                                .format(dbcpu, models))

        session.delete(dbcpu)
        session.flush()

        return
