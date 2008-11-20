#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add model`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.server.dbwrappers.disk_type import get_disk_type
from aquilon.server.dbwrappers.cpu import get_cpu
from aquilon.aqdb.hw.model import Model
from aquilon.aqdb.hw.machine_specs import MachineSpecs


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
        if type not in ["blade", "rackmount", "workstation", "tor_switch",
                        "chassis"]:
            raise ArgumentError("The model's machine type must be blade, rackmount, workstation, tor_switch, or chassis")

        if cputype:
            mem = force_int("mem", mem)
            cpunum = force_int("cpunum", cpunum)
            disksize = force_int("disksize", disksize)
            nics = force_int("nics", nics)

        dbmodel = Model(name=name, vendor=dbvendor, machine_type=type,
                comments=comments)
        try:
            session.save(dbmodel)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add model: %s" % e)

        if cputype:
            dbdisk_type = get_disk_type(session, disktype)
            dbcpu = get_cpu(session, cputype)
            dbmachine_specs = MachineSpecs(model=dbmodel, cpu=dbcpu,
                    cpu_quantity=cpunum, memory=mem, disk_type=dbdisk_type,
                    disk_capacity=disksize, nic_count=nics)
            session.save(dbmachine_specs)
        return


#if __name__=='__main__':
