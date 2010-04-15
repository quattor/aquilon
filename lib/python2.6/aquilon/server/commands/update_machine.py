# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
#
# Copyright (C) 2008,2009,2010  Contributor
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
"""Contains the logic for `aq update machine`."""


from sqlalchemy.exceptions import InvalidRequestError

from aquilon.exceptions_ import (ArgumentError, NotFoundException,
                                 UnimplementedError, IncompleteError)
from aquilon.server.broker import BrokerCommand, force_int
from aquilon.server.dbwrappers.location import get_location
from aquilon.server.dbwrappers.model import get_model
from aquilon.server.dbwrappers.machine import get_machine
from aquilon.server.dbwrappers.system import get_system
from aquilon.server.templates.machine import (PlenaryMachineInfo,
                                              machine_plenary_will_move)
from aquilon.server.templates.cluster import PlenaryCluster
from aquilon.server.templates.host import PlenaryHost
from aquilon.server.templates.base import (compileLock, compileRelease,
                                           PlenaryCollection)
from aquilon.aqdb.model import (Cpu, Chassis, ChassisSlot,
                                Cluster, MachineClusterMember)


class CommandUpdateMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, model, serial, chassis, slot,
               clearchassis, multislot, cluster,
               cpuname, cpuvendor, cpuspeed, cpucount, memory,
               user, **arguments):
        dbmachine = get_machine(session, machine)
        plenaries = PlenaryCollection(logger=logger)

        if clearchassis:
            for dbslot in dbmachine.chassis_slot:
                dbslot.machine = None
                session.add(dbslot)
            session.flush()
            session.refresh(dbmachine)

        remove_plenaries = PlenaryCollection(logger=logger)
        if chassis:
            dbchassis = get_system(session, chassis, Chassis, 'Chassis')
            if machine_plenary_will_move(old=dbmachine.location,
                                         new=dbchassis.chassis_hw.location):
                remove_plenaries.append(PlenaryMachineInfo(dbmachine,
                                                           logger=logger))
            dbmachine.location = dbchassis.chassis_hw.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot information")
            slot = force_int("slot", slot)
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)
        elif slot:
            dbchassis = None
            for dbslot in dbmachine.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Machine in multiple chassis, please "
                                        "use --chassis argument")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information")
            slot = force_int("slot", slot)
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            for dbslot in dbmachine.chassis_slot:
                dbcl = dbslot.chassis.chassis_hw.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("Location %s %s conflicts with chassis %s location %s %s" % (
                                            dblocation.location_type,
                                            dblocation.name,
                                            dbslot.chassis.fqdn,
                                            dbcl.location_type, dbcl.name))
                    else:
                        session.delete(dbslot)
            if machine_plenary_will_move(old=dbmachine.location,
                                         new=dblocation):
                remove_plenaries.append(PlenaryMachineInfo(dbmachine,
                                                           logger=logger))
            dbmachine.location = dblocation

        if model:
            # If overriding model, should probably overwrite default
            # machine specs as well.
            dbmodel = get_model(session, model)
            if dbmodel.machine_type not in ['blade', 'rackmount',
                                            'workstation', 'aurora_node',
                                            'virtual_machine']:
                raise ArgumentError("The update_machine command cannot update "
                                    "machines of type '%s'." %
                                    dbmodel.machine_type)
            # We probably could do this by forcing either cluster or
            # location data to be available as appropriate, but really?
            # Failing seems reasonable.
            if dbmodel.machine_type != dbmachine.model.machine_type and \
               'virtual_machine' in [dbmodel.machine_type,
                                     dbmachine.model.machine_type]:
                raise ArgumentError("Cannot change machine from %s to %s" %
                                    (dbmachine.model.machine_type,
                                     dbmodel.machine_type))
            dbmachine.model = dbmodel

        if cpuname and cpuvendor and cpuspeed:
            cpuspeed = force_int("cpuspeed", cpuspeed)
            q = session.query(Cpu).filter_by(name=cpuname, speed=cpuspeed)
            q = q.join('vendor').filter_by(name=cpuvendor)
            try:
                dbcpu = q.one()
            except InvalidRequestError, e:
                raise ArgumentError("Could not uniquely identify a CPU with name %s, speed %s, and vendor %s: %s" %
                        (cpuname, cpuspeed, cpuvendor, e))
            dbmachine.cpu = dbcpu
        elif cpuname or cpuvendor or cpuspeed:
            raise UnimplementedError("Can only update a machine with an exact cpu (--cpuname, --cpuvendor, and --cpuspeed).")

        if cpucount:
            cpucount = force_int("cpucount", cpucount)
            dbmachine.cpu_quantity = cpucount
        if memory:
            memory = force_int("memory", memory)
            dbmachine.memory=memory
        if serial:
            dbmachine.serial_no=serial

        # FIXME: For now, if a machine has its interface(s) in a portgroup
        # this command will need to be followed by an update_interface to
        # re-evaluate the portgroup for overflow.
        # It would be better to have --pg and --autopg options to let it
        # happen at this point.
        if cluster:
            if not dbmachine.cluster:
                raise ArgumentError("Cannot add an existing machine to "
                                    "a cluster.")
            dbcluster = Cluster.get_unique(session, name=cluster)
            if not dbcluster:
                raise ArgumentError("Could not find cluster named '%s'" %
                                    cluster)
            if dbcluster.metacluster != dbmachine.cluster.metacluster:
                raise ArgumentError("Cannot move machine to a new "
                                    "metacluster: Current metacluster %s "
                                    "does not match new metacluster %s" %
                                    (dbmachine.cluster.metacluster.name,
                                     dbcluster.metacluster.name))
            old_cluster = dbmachine.cluster
            dbmcm = MachineClusterMember.get_unique(session,
                cluster_id=dbmachine.cluster.id, machine_id=dbmachine.id)
            session.delete(dbmcm)
            session.flush()
            # Without these refreshes the MCM creation below fails...
            # presumably because the old linkage is still cached somewhere?
            session.refresh(dbmachine)
            session.refresh(old_cluster)
            dbmcm = MachineClusterMember(cluster=dbcluster, machine=dbmachine)
            session.add(dbmcm)
            session.flush()
            session.refresh(dbmachine)
            session.refresh(dbcluster)
            if hasattr(dbcluster, 'verify_ratio'):
                dbcluster.verify_ratio()
            dbmachine.location = dbcluster.location_constraint
            plenaries.append(PlenaryCluster(old_cluster, logger=logger))
            plenaries.append(PlenaryCluster(dbcluster, logger=logger))

        session.add(dbmachine)
        session.flush()

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))
        if remove_plenaries.plenaries and dbmachine.host:
            plenaries.append(PlenaryHost(dbmachine.host, logger=logger))
        try:
            compileLock(logger=logger)
            remove_plenaries.stash()
            plenaries.write(locked=True)
            remove_plenaries.remove(locked=True)

            if dbmachine.host:
                # XXX: May need to reconfigure.
                pass
        except:
            plenaries.restore_stash()
            remove_plenaries.restore_stash()
            raise
        finally:
            compileRelease(logger=logger)

        return

    def adjust_slot(self, session, logger,
                    dbmachine, dbchassis, slot, multislot):
        for dbslot in dbmachine.chassis_slot:
            # This update is a noop, ignore.
            # Technically, this could be a request to trim the list down
            # to just this one slot - in that case --clearchassis will be
            # required.
            if dbslot.chassis == dbchassis and dbslot.slot_number == slot:
                return
        if len(dbmachine.chassis_slot) > 1 and not multislot:
            raise ArgumentError("Use --multislot to support a machine in more "
                                "than one slot, or --clearchassis to remove "
                                "current chassis slot information.")
        if not multislot:
            for dbslot in dbmachine.chassis_slot:
                logger.info("Clearing machine %s out of chassis %s slot %d" %
                            (dbmachine.name, dbslot.chassis.fqdn,
                             dbslot.slot_number))
                dbslot.machine = None
        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.machine:
                raise ArgumentError("Chassis %s slot %d already has machine "
                                    "%s" % (dbchassis.fqdn, slot,
                                            dbslot.machine.name))
            dbslot.machine = dbmachine
            session.add(dbslot)
        else:
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot,
                                 machine=dbmachine)
            session.add(dbslot)
        return
