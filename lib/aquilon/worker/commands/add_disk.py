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
"""Contains the logic for `aq add disk`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Machine, Disk, LocalDisk, VirtualDisk, Share,
                                Filesystem)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import find_resource
from aquilon.worker.templates import Plenary


class CommandAddDisk(BrokerCommand):
    """Add a disk object (local or share) to a machine"""

    required_parameters = ["machine", "disk", "size", "controller"]

    def render(self, session, logger, machine, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, wwn, bus_address, **kw):
        if controller not in controller_types:
            raise ArgumentError("%s is not a valid controller type, use one "
                                "of: %s." % (controller,
                                             ", ".join(controller_types)))

        dbmachine = Machine.get_unique(session, machine, compel=True)
        for dbdisk in dbmachine.disks:
            if dbdisk.device_name == disk:
                raise ArgumentError("Machine %s already has a disk named %s." %
                                    (machine, disk))
            if dbdisk.bootable:
                if boot is None:
                    boot = False
                elif boot:
                    raise ArgumentError("Machine %s already has a boot disk." %
                                        machine)

        if wwn:
            dbdisk = session.query(Disk).filter_by(wwn=wwn).first()
            if dbdisk:
                raise ArgumentError("WWN {0!s} is already in use by disk {1!s} "
                                    "of {2:l}.".format(wwn, dbdisk,
                                                       dbdisk.machine))

        if boot is None:
            # Backward compatibility: "sda"/"c0d0" is bootable, except if there
            # is already a boot disk
            boot = (disk == "sda" or disk == "c0d0")

        cls = LocalDisk
        extra_params = {}
        if share or filesystem:
            if not dbmachine.vm_container:
                raise ArgumentError("{0} is not a virtual machine, it is not "
                                    "possible to define a virtual disk."
                                    .format(dbmachine))

            if share:
                res_cls = Share
                res_name = share
            else:
                res_cls = Filesystem
                res_name = filesystem

            dbres = find_resource(res_cls,
                                  dbmachine.vm_container.holder.holder_object,
                                  resourcegroup, res_name)
            extra_params["backing_store"] = dbres
            extra_params["snapshotable"] = snapshot
            cls = VirtualDisk

        dbdisk = cls(device_name=disk, controller_type=controller,
                     capacity=size, bootable=boot, wwn=wwn, address=address,
                     bus_address=bus_address, comments=comments, **extra_params)

        dbmachine.disks.append(dbdisk)

        plenary_info = Plenary.get_plenary(dbmachine, logger=logger)
        plenary_info.write()

        return
