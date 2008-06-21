#!/ms/dist/python/PROJ/core/2.5.0/bin/python
# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# $Header$
# $Change$
# $DateTime$
# $Author$
# Copyright (C) 2008 Morgan Stanley
#
# This module is part of Aquilon
"""Contains the logic for `aq add machine`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.server.broker import (format_results, add_transaction, az_check,
                                   BrokerCommand)
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.aqdb.hardware import Machine, Cpu
from aquilon.server.templates import PlenaryMachineInfo


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    @add_transaction
    @az_check
    # arguments will contain one of --chassis --rack or --desk
    def render(self, session, machine, model, serial,
            cpuname, cpuvendor, cpuspeed, cpucount, memory,
            user, **arguments):
        dblocation = get_location(session, **arguments)
        dbmodel = get_model(session, model)

        if cpuspeed is not None:
            cpuspeed = self.force_int("cpuspeed", cpuspeed)

        # Figure out a CPU...
        dbcpu = None
        if not (cpuname or cpuspeed or cpuvendor):
            if not dbmodel.specifications:
                ArgumentError("Model %s does not have machine specification defaults, please specify --cpuvendor, --cpuname, and --cpuspeed." %
                        model)
            dbcpu = dbmodel.specifications.cpu
        else:
            # Was there enough on the command line to specify one?
            q = session.query(Cpu)
            if cpuname:
                q = q.filter(Cpu.name.like(cpuname.lower() + '%'))
            if cpuspeed:
                q = q.filter_by(speed=cpuspeed)
            if cpuvendor:
                q = q.join('vendor').filter_by(name=cpuvendor.lower())
            cpulist = q.all()
            if not cpulist:
                raise ArgumentError("Could not find a cpu with the given attributes.")
            if len(cpulist) == 1:
                # Found it exactly.
                dbcpu = cpulist[0]
            elif dbmodel.specifications:
                # Not exact, but see if the specs match the default.
                dbcpu = dbmodel.specifications.cpu
                if ((cpuname and not dbcpu.name.startswith(cpuname.lower))
                        or (cpuspeed and dbcpu.speed != cpuspeed)
                        or (cpuvendor and
                            dbcpu.vendor.name != cpuvendor.lower())):
                    raise ArgumentError("Could not uniquely identify a cpu with the attributes given.")
            else:
                raise ArgumentError("Could not uniquely identify a cpu with the attributes given.")
        
        if cpucount is not None:
            cpucount = self.force_int("cpucount", cpucount)
        if cpucount is None:
            if dbmodel.specifications:
                cpucount = dbmodel.specifications.cpu_quantity
            else:
                ArgumentError("Model %s does not have machine specification defaults, please specify --cpucount." %
                        model)
        else:
            cpucount = self.force_int("cpucount", cpucount)

        if memory is None:
            if dbmodel.specifications:
                memory = dbmodel.specifications.memory
            else:
                ArgumentError("Model %s does not have machine specification defaults, please specify --memory (in MB)." %
                        model)
        else:
            memory = self.force_int("memory", memory)

        dbmachine = Machine(dblocation, dbmodel, name=machine, cpu=dbcpu,
                cpu_quantity=cpucount, memory=memory, serial_no=serial)
        session.save(dbmachine)
        session.flush()

        plenary_info = PlenaryMachineInfo(dbmachine)
        plenary_info.write(self.config.get("broker", "plenarydir"),
                self.config.get("broker", "servername"), user)
        return

    # FIXME: This utility method may be better suited elsewhere.
    def force_int(self, label, value):
        if value is None:
            return None
        try:
            result = int(value)
        except Exception, e:
            raise ArgumentError("Expected an integer for %s: %s" % (label, e))
        return result


#if __name__=='__main__':
