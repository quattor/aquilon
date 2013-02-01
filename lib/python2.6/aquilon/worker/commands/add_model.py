# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011  Contributor
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
                         "chassis", "virtual_machine", "nic"]
        if type not in allowed_types:
            raise ArgumentError("The model's machine type must be one of: %s." %
                                ", ".join(allowed_types))

        # Handle the deprecated cputype parameter
        if arguments.get("cputype", None):
            self.deprecated_option("cputype", "Please use --cpuname instead.",
                                   **arguments)
            cpuname = arguments["cputype"]

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
