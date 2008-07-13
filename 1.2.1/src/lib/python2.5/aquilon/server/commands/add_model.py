#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add model`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand, force_int)
from aquilon.server.dbwrappers.vendor import get_vendor
from aquilon.aqdb.hw.model import Model
from aquilon.aqdb.hw.machine_specs import MachineSpecs


class CommandAddModel(BrokerCommand):

    required_parameters = ["name", "vendor", "type"]

    @add_transaction
    @az_check
    def render(self, session, name, vendor, type,
            cputype, cpunum, mem, disktype, disksize, nics,
            comments, **arguments):
        dbmodel = session.query(Model).filter_by(name=name).first()
        if dbmodel is not None:
            raise ArgumentError('Specified model already exists')
        dbvendor = get_vendor(session, vendor)
        dbmachine_type = get_machine_type(session, type)

        if cputype:
            mem = force_int("mem", mem)
            cpunum = force_int("cpunum", cpunum)
            disksize = force_int("disksize", disksize)
            nics = force_int("nics", nics)

        # FIXME: Model cannot (yet) take comments in __init__
        # Should be fixed when Model moves over to declarative
        dbmodel = Model(name, dbvendor, dbmachine_type)
        if comments:
            dbmodel.comments = comments
        try:
            session.save(dbmodel)
        except InvalidRequestError, e:
            raise ArgumentError("Could not add model: %s" % e)

        # FIXME: Hack that can be removed when declarative used for Model
        session.flush()
        session.refresh(dbmodel)

        if cputype:
            dbmachine_specs = MachineSpecs(model=dbmodel, cpu=cputype,
                    cpu_quantity=cpunum, memory=mem, disk_type=disktype,
                    disk_capacity=disksize, nic_count=nics)
            session.save(dbmachine_specs)
        return


#if __name__=='__main__':
