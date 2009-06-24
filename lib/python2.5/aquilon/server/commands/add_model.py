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
"""Contains the logic for `aq add model`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.server.dbwrappers.cpu import get_cpu
from aquilon.aqdb.model import Model, MachineSpecs


class CommandAddModel(BrokerCommand):

    required_parameters = ["name", "vendor", "type"]

    def render(self, session, name, vendor, type,
            cputype, cpunum, mem, disktype, disksize, nics,
            comments, **arguments):
        dbmodel = session.query(Model).filter_by(name=name).first()
        if dbmodel is not None:
            raise ArgumentError('Specified model already exists')
        dbvendor = get_vendor(session, vendor)

        # Specifically not allowing new models to be added that are of
        # type aurora_node - that is only meant for the dummy aurora_model.
        allowed_types = ["blade", "rackmount", "workstation", "tor_switch",
                         "chassis", "virtual_machine"]
        if type not in allowed_types:
            raise ArgumentError("The model's machine type must be one of %s" %
                                allowed_types)

        if cputype:
            mem = force_int("mem", mem)
            cpunum = force_int("cpunum", cpunum)
            disksize = force_int("disksize", disksize)
            nics = force_int("nics", nics)

        dbmodel = Model(name=name, vendor=dbvendor, machine_type=type,
                comments=comments)
        try:
            session.add(dbmodel)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add model: %s" % e)

        if cputype:
            dbdisk_type = get_disk_type(session, disktype)
            dbcpu = get_cpu(session, cputype)
            dbmachine_specs = MachineSpecs(model=dbmodel, cpu=dbcpu,
                    cpu_quantity=cpunum, memory=mem, disk_type=dbdisk_type,
                    disk_capacity=disksize, nic_count=nics)
            session.add(dbmachine_specs)
        return
