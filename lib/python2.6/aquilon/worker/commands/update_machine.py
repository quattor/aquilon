# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2008,2009,2010,2011,2012,2013  Contributor
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


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.hardware_entity import update_primary_ip
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.templates.machine import machine_plenary_will_move
from aquilon.worker.templates.base import Plenary, PlenaryCollection
from aquilon.worker.locks import lock_queue, CompileKey
from aquilon.worker.processes import DSDBRunner
from aquilon.aqdb.model import (Cpu, Chassis, ChassisSlot, Model, Cluster,
                                Machine, ClusterResource)


class CommandUpdateMachine(BrokerCommand):

    required_parameters = ["machine"]

    def render(self, session, logger, machine, model, vendor, serial,
               chassis, slot, clearchassis, multislot,
               cluster, allow_metacluster_change,
               cpuname, cpuvendor, cpuspeed, cpucount, memory, ip,
               **arguments):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        plenaries = PlenaryCollection(logger=logger)
        oldinfo = DSDBRunner.snapshot_hw(dbmachine)

        if clearchassis:
            del dbmachine.chassis_slot[:]

        remove_plenaries = PlenaryCollection(logger=logger)
        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            if machine_plenary_will_move(old=dbmachine.location,
                                         new=dbchassis.location):
                remove_plenaries.append(Plenary.get_plenary(dbmachine))
            dbmachine.location = dbchassis.location
            if slot is None:
                raise ArgumentError("Option --chassis requires --slot "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)
        elif slot is not None:
            dbchassis = None
            for dbslot in dbmachine.chassis_slot:
                if dbchassis and dbslot.chassis != dbchassis:
                    raise ArgumentError("Machine in multiple chassis, please "
                                        "use --chassis argument.")
                dbchassis = dbslot.chassis
            if not dbchassis:
                raise ArgumentError("Option --slot requires --chassis "
                                    "information.")
            self.adjust_slot(session, logger,
                             dbmachine, dbchassis, slot, multislot)

        dblocation = get_location(session, **arguments)
        if dblocation:
            loc_clear_chassis = False
            for dbslot in dbmachine.chassis_slot:
                dbcl = dbslot.chassis.location
                if dbcl != dblocation:
                    if chassis or slot is not None:
                        raise ArgumentError("{0} conflicts with chassis {1!s} "
                                            "location {2}.".format(dblocation,
                                                        dbslot.chassis, dbcl))
                    else:
                        loc_clear_chassis = True
            if loc_clear_chassis:
                del dbmachine.chassis_slot[:]
            if machine_plenary_will_move(old=dbmachine.location,
                                         new=dblocation):
                remove_plenaries.append(Plenary.get_plenary(dbmachine))
            dbmachine.location = dblocation

        if model or vendor:
            # If overriding model, should probably overwrite default
            # machine specs as well.
            if not model:
                model = dbmachine.model.name
            if not vendor:
                vendor = dbmachine.model.vendor.name
            dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                       compel=True)
            if dbmodel.machine_type not in ['blade', 'rackmount',
                                            'workstation', 'aurora_node',
                                            'virtual_machine']:
                raise ArgumentError("The update_machine command cannot update "
                                    "machines of type %s." %
                                    dbmodel.machine_type)
            # We probably could do this by forcing either cluster or
            # location data to be available as appropriate, but really?
            # Failing seems reasonable.
            if dbmodel.machine_type != dbmachine.model.machine_type and \
               'virtual_machine' in [dbmodel.machine_type,
                                     dbmachine.model.machine_type]:
                raise ArgumentError("Cannot change machine from %s to %s." %
                                    (dbmachine.model.machine_type,
                                     dbmodel.machine_type))

            old_nic_model = dbmachine.model.nic_model
            new_nic_model = dbmodel.nic_model
            if old_nic_model != new_nic_model:
                for iface in dbmachine.interfaces:
                    if iface.model == old_nic_model:
                        iface.model = new_nic_model

            dbmachine.model = dbmodel

        if cpuname or cpuvendor or cpuspeed is not None:
            dbcpu = Cpu.get_unique(session, name=cpuname, vendor=cpuvendor,
                                   speed=cpuspeed, compel=True)
            dbmachine.cpu = dbcpu

        if cpucount is not None:
            dbmachine.cpu_quantity = cpucount
        if memory is not None:
            dbmachine.memory = memory
        if serial:
            dbmachine.serial_no = serial

        if ip:
            update_primary_ip(session, dbmachine, ip)

        # FIXME: For now, if a machine has its interface(s) in a portgroup
        # this command will need to be followed by an update_interface to
        # re-evaluate the portgroup for overflow.
        # It would be better to have --pg and --autopg options to let it
        # happen at this point.
        if cluster:
            if not dbmachine.cluster:
                raise ArgumentError("Cannot add an existing machine to "
                                    "a cluster.")
            dbcluster = Cluster.get_unique(session, name=cluster, compel=True)
            if dbcluster.metacluster != dbmachine.cluster.metacluster \
               and not allow_metacluster_change:
                raise ArgumentError("Cannot move machine to a new "
                                    "metacluster: Current {0:l} does not match "
                                    "new {1:l}.".format(dbmachine.cluster.metacluster,
                                                        dbcluster.metacluster))
            old_cluster = dbmachine.cluster
            if not dbcluster.resholder:
                dbcluster.resholder = ClusterResource(cluster=dbcluster)
                # We need the ID of the resholder object...
                session.flush()
            remove_plenaries.append(Plenary.get_plenary(dbmachine.vm_container))
            dbmachine.vm_container.holder_id = dbcluster.resholder.id
            session.expire(dbmachine.vm_container, ["holder"])
            dbmachine.location = dbcluster.location_constraint
            session.flush()
            plenaries.append(Plenary.get_plenary(old_cluster))
            plenaries.append(Plenary.get_plenary(dbcluster))

        if dbmachine.vm_container:
            plenaries.append(Plenary.get_plenary(dbmachine.vm_container))

        session.flush()

        # Check if the changed parameters still meet cluster capacity
        # requiremets
        if dbmachine.cluster:
            dbmachine.cluster.validate()
            if allow_metacluster_change:
                dbmachine.cluster.metacluster.validate()
        if dbmachine.host and dbmachine.host.cluster:
            dbmachine.host.cluster.validate()

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenaries.append(Plenary.get_plenary(dbmachine))
        if remove_plenaries.plenaries and dbmachine.host:
            plenaries.append(Plenary.get_plenary(dbmachine.host))

        key = CompileKey.merge([plenaries.get_write_key(),
                                remove_plenaries.get_remove_key()])
        try:
            lock_queue.acquire(key)
            remove_plenaries.stash()
            plenaries.write(locked=True)
            remove_plenaries.remove(locked=True)

            if dbmachine.host:
                # XXX: May need to reconfigure.
                pass

            dsdb_runner = DSDBRunner(logger=logger)
            dsdb_runner.update_host(dbmachine, oldinfo)
            dsdb_runner.commit_or_rollback("Could not update machine in DSDB")
        except:
            plenaries.restore_stash()
            remove_plenaries.restore_stash()
            raise
        finally:
            lock_queue.release(key)

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
            slots = ", ".join([str(dbslot.slot_number) for dbslot in
                               dbmachine.chassis_slot])
            logger.info("Clearing {0:l} out of {1:l} slot(s) "
                        "{2}".format(dbmachine, dbchassis, slots))
            del dbmachine.chassis_slot[:]
        q = session.query(ChassisSlot)
        q = q.filter_by(chassis=dbchassis, slot_number=slot)
        dbslot = q.first()
        if dbslot:
            if dbslot.machine:
                raise ArgumentError("{0} slot {1} already has machine "
                                    "{2}.".format(dbchassis, slot,
                                                  dbslot.machine.label))
        else:
            dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
        dbmachine.chassis_slot.append(dbslot)

        return
