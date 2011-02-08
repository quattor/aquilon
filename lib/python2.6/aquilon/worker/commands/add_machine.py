# ex: set expandtab softtabstop=4 shiftwidth=4: -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
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
"""Contains the logic for `aq add machine`."""


from aquilon.exceptions_ import ArgumentError
from aquilon.worker.broker import BrokerCommand
from aquilon.worker.dbwrappers.location import get_location
from aquilon.worker.dbwrappers.machine import create_machine
from aquilon.worker.templates.base import PlenaryCollection
from aquilon.worker.templates.machine import PlenaryMachineInfo
from aquilon.worker.templates.cluster import PlenaryCluster
from aquilon.aqdb.model import (Chassis, ChassisSlot, Cluster, Model, Machine)


class CommandAddMachine(BrokerCommand):

    required_parameters = ["machine", "model"]

    # arguments will contain one of --chassis --rack or --desk
    def render(self, session, logger, machine, model, vendor, serial, chassis,
               slot, cpuname, cpuvendor, cpuspeed, cpucount, memory, cluster,
               comments, **arguments):
        dblocation = get_location(session, **arguments)
        if chassis:
            dbchassis = Chassis.get_unique(session, chassis, compel=True)
            if slot is None:
                raise ArgumentError("The --chassis option requires a --slot.")
            if dblocation and dblocation != dbchassis.location:
                raise ArgumentError("{0} conflicts with chassis location "
                                    "{1}.".format(dblocation, dbchassis.location))
            dblocation = dbchassis.location
        elif slot is not None:
            raise ArgumentError("The --slot option requires a --chassis.")

        dbmodel = Model.get_unique(session, name=model, vendor=vendor,
                                   compel=True)

        if dbmodel.machine_type not in ['blade', 'rackmount', 'workstation',
                                        'aurora_node', 'virtual_machine']:
            raise ArgumentError("The add_machine command cannot add machines "
                                "of type %(type)s.  Try 'add %(type)s'." %
                    {"type": dbmodel.machine_type})

        if cluster:
            if dbmodel.machine_type != 'virtual_machine':
                raise ArgumentError("Only virtual machines can have a cluster "
                                    "attribute.")
            dbcluster = Cluster.get_unique(session, cluster,
                                           compel=ArgumentError)
            # This test could be either archetype or cluster_type
            if dbcluster.personality.archetype.name != 'esx_cluster':
                raise ArgumentError("Can only add virtual machines to "
                                    "clusters with archetype esx_cluster.")
            if dblocation and dbcluster.location_constraint != dblocation:
                raise ArgumentError("Cannot override cluster location {0} "
                                    "with location {1}.".format(
                                        dbcluster.location_constraint,
                                        dblocation))
            dblocation = dbcluster.location_constraint
        elif dbmodel.machine_type == 'virtual_machine':
            raise ArgumentError("Virtual machines must be assigned to a "
                                "cluster.")

        Machine.get_unique(session, machine, preclude=True)
        dbmachine = create_machine(session, machine, dblocation, dbmodel,
                                   cpuname, cpuvendor, cpuspeed, cpucount,
                                   memory, serial, comments)

        if chassis:
            # FIXME: Are virtual machines allowed to be in a chassis?
            dbslot = session.query(ChassisSlot).filter_by(chassis=dbchassis,
                    slot_number=slot).first()
            if not dbslot:
                dbslot = ChassisSlot(chassis=dbchassis, slot_number=slot)
            dbslot.machine = dbmachine
            session.add(dbslot)
        if cluster:
            dbcluster.machines.append(dbmachine)
            session.flush()

        session.flush()

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(PlenaryMachineInfo(dbmachine, logger=logger))
        if cluster:
            plenaries.append(PlenaryCluster(dbcluster, logger=logger))

        # The check to make sure a plenary file is not written out for
        # dummy aurora hardware is within the call to write().  This way
        # it is consistent without altering (and forgetting to alter)
        # all the calls to the method.
        plenaries.write()
        return
