# -*- cpy-indent-level: 4; indent-tabs-mode: nil -*-
# ex: set expandtab softtabstop=4 shiftwidth=4:
#
# Copyright (C) 2013  Contributor
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
"""Contains the logic for `aq update disk`."""

from aquilon.exceptions_ import ArgumentError
from aquilon.aqdb.model import (Machine, Disk, VirtualDisk, VirtualLocalDisk,
                                Filesystem)
from aquilon.aqdb.model.disk import controller_types
from aquilon.worker.broker import BrokerCommand  # pylint: disable=W0611
from aquilon.worker.dbwrappers.resources import find_share
from aquilon.worker.templates import Plenary, PlenaryCollection


def copy_virt_disk(session, cls, orig):
    # Pass machine_id, not machine - passing machine would pull the object into
    # the session, which we do not want yet
    new_disk = cls(capacity=orig.capacity, device_name=orig.device_name,
                   controller_type=orig.controller_type, address=orig.address,
                   machine_id=orig.machine_id, bootable=orig.bootable,
                   comments=orig.comments, snapshotable=orig.snapshotable)

    assert new_disk not in session
    return new_disk


class CommandUpdateDisk(BrokerCommand):

    required_parameters = ["machine", "disk"]

    def render(self, session, logger, machine, disk, controller, share,
               filesystem, resourcegroup, address, comments, size, boot,
               snapshot, rename_to, **kw):
        dbmachine = Machine.get_unique(session, machine, compel=True)
        dbdisk = Disk.get_unique(session, device_name=disk, machine=dbmachine,
                                 compel=True)

        plenaries = PlenaryCollection(logger=logger)
        plenaries.append(Plenary.get_plenary(dbmachine))

        if rename_to:
            Disk.get_unique(session, device_name=rename_to, machine=dbmachine,
                            preclude=True)
            dbdisk.device_name = rename_to

        if comments is not None:
            dbdisk.comments = comments

        if size is not None:
            dbdisk.capacity = size

        if controller:
            if controller not in controller_types:
                raise ArgumentError("%s is not a valid controller type, use "
                                    "one of: %s." %
                                    (controller, ", ".join(controller_types)))
            dbdisk.controller_type = controller

        if boot is not None:
            dbdisk.bootable = boot
            # There should be just one boot disk. We may need to re-think this
            # if we want to model software RAID in the database.
            for disk in dbmachine.disks:
                if disk == dbdisk:
                    continue
                if boot and disk.bootable:
                    disk.bootable = False

        if address:
            # TODO: do we really care? Bus address makes sense for physical
            # disks as well, even if we cannot use that information today.
            if not isinstance(dbdisk, VirtualDisk) and \
               not isinstance(dbdisk, VirtualLocalDisk):
                raise ArgumentError("Bus address can only be set for virtual "
                                    "disks.")
            dbdisk.address = address

        if snapshot is not None:
            if not isinstance(dbdisk, VirtualDisk) and \
               not isinstance(dbdisk, VirtualLocalDisk):
                raise ArgumentError("Snapshot capability can only be set for "
                                    "virtual disks.")
            dbdisk.snapshotable = snapshot

        if share or filesystem:
            if isinstance(dbdisk, VirtualDisk):
                old_share = dbdisk.share
                old_share.disks.remove(dbdisk)
            elif isinstance(dbdisk, VirtualLocalDisk):
                old_fs = dbdisk.filesystem
                old_fs.disks.remove(dbdisk)
            else:
                raise ArgumentError("Disk {0!s} of {1:l} is not a virtual "
                                    "disk, changing the backend store is not "
                                    "possible.".format(dbdisk, dbmachine))

            if share:
                if not isinstance(dbdisk, VirtualDisk):
                    new_dbdisk = copy_virt_disk(session, VirtualDisk, dbdisk)
                    session.delete(dbdisk)
                    session.flush()
                    session.add(new_dbdisk)
                    dbdisk = new_dbdisk

                new_share = find_share(dbmachine.vm_container.holder.holder_object,
                                       resourcegroup, share)
                new_share.disks.append(dbdisk)

            if filesystem:
                if not isinstance(dbdisk, VirtualLocalDisk):
                    new_dbdisk = copy_virt_disk(session, VirtualLocalDisk, dbdisk)
                    session.delete(dbdisk)
                    session.flush()
                    session.add(new_dbdisk)
                    dbdisk = new_dbdisk

                new_fs = Filesystem.get_unique(session, name=filesystem,
                                               holder=dbmachine.vm_container.holder,
                                               compel=True)
                new_fs.disks.append(dbdisk)

        session.flush()

        plenaries.write()

        return
